#!/usr/bin/env python3
"""Measure complete actor chat templates from a local tokenizer; never downloads.

Example: python measure_histories.py families.jsonl --out measures.json \\
  --tokenizer /absolute/path/to/tokenizer/snapshot
Message hashes use UTF-8 JSON with sorted keys, no ASCII escaping or whitespace.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

SYSTEM_PREFIX = '你在进行虚构人物对话。依据人物设定、自己的经历和可见信息自然回应，不输出决策标签。\n'
NEUTRAL_USER = '请继续。'


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_hashes(path):
    # Include every common tokenizer configuration and vocabulary asset that exists.
    names = ('tokenizer_config.json', 'tokenizer.json', 'special_tokens_map.json',
             'added_tokens.json', 'vocab.json', 'merges.txt', 'vocab.txt',
             'tokenizer.model', 'spiece.model', 'sentencepiece.bpe.model',
             'chat_template.jinja', 'config.json')
    return {name: sha((path / name).read_bytes()) for name in names if (path / name).is_file()}


def message_counter(messages):
    return Counter(canonical(message) for message in messages)


def measure_family(family, tokenizer):
    histories = family['histories']
    if len(histories) != 2:
        raise ValueError(f"{family['family_id']}: expected exactly two histories")
    blocks = family['blocks']
    block_by_id = {block['id']: block for block in blocks}
    if len(block_by_id) != len(blocks):
        raise ValueError(f"{family['family_id']}: duplicate block ID")
    block_records = []
    for block in blocks:
        data = canonical(block['messages'])
        block_records.append({'id': block['id'], 'messages_sha256': sha(data),
                              'messages_bytes': len(data), 'message_count': len(block['messages'])})
    if family['history_mode'] == 'exact_permutation':
        if not blocks:
            raise ValueError(f"{family['family_id']}: exact permutation has no blocks")
        for history in histories:
            if Counter(history['block_order']) != Counter(block_by_id.keys()):
                raise ValueError(f"{family['family_id']}: {history['id']} block order is not a permutation")
            assembled = [m for bid in history['block_order'] for m in block_by_id[bid]['messages']]
            if canonical(assembled) != canonical(history['messages']):
                raise ValueError(f"{family['family_id']}: {history['id']} does not match its source blocks")
        if message_counter(histories[0]['messages']) != message_counter(histories[1]['messages']):
            raise ValueError(f"{family['family_id']}: history message multisets differ")
    system = SYSTEM_PREFIX + family['persona']['natural_profile'] + '\n' + family['common_visible_context']
    results, token_sequences = [], []
    for history in histories:
        messages = ([{'role': 'system', 'content': system}] + history['messages'] +
                    [{'role': 'user', 'content': NEUTRAL_USER}])
        ids = list(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True))
        token_sequences.append(ids)
        results.append({'history_id': history['id'], 'block_order': history['block_order'],
                        'message_count': len(history['messages']), 'actor_messages_sha256': sha(canonical(messages)),
                        'token_count': len(ids), 'token_ids_sha256': sha(canonical(ids))})
    comparison = None
    if family['history_mode'] == 'exact_permutation':
        a, b = token_sequences
        comparison = {'message_multisets_equal': True, 'token_lengths_equal': len(a) == len(b),
                      'token_id_multisets_equal': Counter(a) == Counter(b),
                      'token_sequences_equal': a == b}
    return {'family_id': family['family_id'], 'history_mode': family['history_mode'],
            'blocks': block_records, 'histories': results, 'exact_permutation_comparison': comparison}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('families', type=Path, help='Final family JSONL input')
    parser.add_argument('--out', required=True, type=Path, help='Measurement JSON output')
    parser.add_argument('--tokenizer', required=True, type=Path, help='Local tokenizer directory')
    args = parser.parse_args()
    path = args.tokenizer.expanduser().resolve(strict=True)
    if not path.is_dir():
        parser.error('--tokenizer must be a local directory')
    if args.families.resolve() == args.out.resolve():
        parser.error('input and output must be different files')
    try:
        import transformers
        import tokenizers
        from transformers import AutoTokenizer
    except ImportError as exc:
        parser.error(f'Transformers and tokenizers are required for full chat-template measurement: {exc}')
    tokenizer = AutoTokenizer.from_pretrained(str(path), local_files_only=True, trust_remote_code=False)
    template = tokenizer.chat_template
    if not template:
        parser.error('tokenizer has no chat template; no full actor-template measurement possible')
    template_bytes = template.encode('utf-8') if isinstance(template, str) else canonical(template)
    results = []
    with args.families.open(encoding='utf-8') as inp:
        for lineno, line in enumerate(inp, 1):
            if not line.strip():
                continue
            try:
                results.append(measure_family(json.loads(line), tokenizer))
            except Exception as exc:
                raise ValueError(f'{args.families}:{lineno}: {exc}') from exc
    if not results:
        parser.error('input contains no families')
    output = {'measurement': 'full_actor_chat_template', 'tokenizer_path': str(path),
              'tokenizer_class': type(tokenizer).__name__, 'transformers_version': transformers.__version__,
              'tokenizers_version': tokenizers.__version__, 'tokenizer_file_sha256': file_hashes(path),
              'chat_template_sha256': sha(template_bytes),
              'serialization': 'UTF-8 JSON, sort_keys=true, ensure_ascii=false, compact separators',
              'add_generation_prompt': True, 'neutral_user': NEUTRAL_USER,
              'input_sha256': sha(args.families.read_bytes()), 'families': results}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
