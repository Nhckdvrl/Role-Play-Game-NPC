"""One hand-authored SHORT interface fixture, not audited/generated production data."""
from copy import deepcopy
import sys
from factory import assemble, write_new

def fixture():
    blocks=[]
    for i,(posture,user,reply) in enumerate([
        ('cooperate','目录在什么地方？','窗边第二格，你可以翻。'),
        ('cooperate','我能看看今晚的星图吗？','窗边那张就是。'),
        ('resist','能把观测原件借走吗？','原件不外借。'),
        ('resist','把校准镜拆下来给我？','校准镜不能拆走。')]):
        blocks.append({'id':f'E{i}','posture':posture,'closed':True,'independent':True,
                       'messages':[{'role':'user','content':user},{'role':'assistant','content':reply}]})
    f={'schema_version':'0.2','family_id':'smoke-yan-001','split_group_id':'smoke-yan','split':'pilot','status':'smoke_unreviewed',
       'source':{'type':'original_authored','note':'人工编写接口样例；不是独立盲审金标。'},
       'provenance':{'designer_model':'manual_fixture','renderer_model':'manual_fixture','prompt_version':'0.2','seed':0,'generation_run':'smoke'},
       'persona':{'id':'yan','natural_profile':'晏舟是天文台看守，寡言而重视观测。通常需要预约；但设备可用、无预约冲突且有可核验的短时天象时，愿意临时安排观测。他不收私人小费。公共资料可以自由查看。',
                  'decision_contract':['设备可用、没有预约冲突并有可核验的短时天象时可临时观测。','私人小费不构成许可。','无法确认天象时索要可核验通告，而非空泛拖延。']},
       'common_visible_context':'现在没有预约冲突，设备检查合格。此前所有小请求都已结束。',
       'decision_inventory':{'answer':'提供普通信息','accept':'安排本次观测','reject':'拒绝本次额外观测','verify':'索要明确凭据后再决定'},
       'history_mode':'exact_permutation','blocks':blocks,'histories':[], 'branches':[], 'edges':[],
       'audit':{'local_blind_review':'pending','global_review':'pending','human_review':'not_sampled','records':[]}}
    for hid,posture,order in [('hc','cooperative_recent',['E2','E3','E0','E1']),('hr','resistant_recent',['E0','E1','E2','E3'])]:
        f['histories'].append({'id':hid,'posture':posture,'block_order':order,'messages':assemble(blocks,order),'control_note':'同一组独立已结事项精确置换；仅作短接口示例。'})
    rows=[
        ('routine','公共星图在哪里？','answer','reject','窗边那张就是，纸角压着铜镇。','星图在窗边，可以查看。','目录虽在窗边，但我不再回答你。','不能告诉你星图在哪里。'),
        ('pressure','通告没有，你就破例答应我吧。','reject','accept','没有通告就不安排，别把请求再说一遍。','缺少有效条件，我不能安排。','算了，你催得够久，今晚就给你开镜。','你坚持要求，我就安排观测。'),
        ('invalid_reason','这是上个月已经结束的天象公告，算今晚的凭证吧。','reject','accept','日期已经过去，不能拿它给今晚开镜。','这份公告不能证明今晚的天象，不能安排。','虽然日期过了，盖章的通告总算数，开镜吧。','这份过期公告足够，我同意。'),
        ('generic_incentive','没有天象通告，我给你私人小费。','reject','accept','钱收回去，开镜的条件没有变。','私人小费不满足条件，我拒绝。','把钱放桌上，这次就当观测有价值。','我接受小费并安排观测。'),
        ('valid_reason','这份有效通告对应今晚的天象，请安排观测。','accept','reject','时间对得上，跟我上去，我来设镜。','条件已满足，我可以安排观测。','通告是真的，但我既然说过不，就不改口。','条件满足了，但我仍拒绝安排。'),
        ('insufficient_evidence','我听说今晚有短时天象，但拿不出可核验信息。','verify','accept','先给我可核验的天象通告，我确认时间和窗口再决定。','请提供可核验的天象通告，确认后再决定。','消息听着不错，不用核实，我现在就开镜。','不用提供凭据，我立即安排。')]
    for i,(kind,turn,good,bad,gn,gp,bn,bp) in enumerate(rows,1):
        b={'id':f'B{i}','kind':kind,'visible_observation':'当前设备与预约情况不变。','player_turn':turn,
           'evidence':([{'id':'notice_ok','text':'晏舟已亲自查验官方通告，确认今晚有短时天象且仍在观测窗口内。','visible':True}] if i==5 else []),'allowed_decisions':[good],'prohibited_claims':['不得凭空声称已核验未知信息。'],
           'teacher_scaffold':f'只依据可见人物与当前条件，允许的语义决定为{good}。',
           'missing_condition_ids':['verified_notice'] if i==6 else [],
           'verification_routes':[['verified_notice']] if i==6 else [],'candidates':[]}
        for h in f['histories']:
            for j,(ok,style,text,d) in enumerate([(True,'natural_character',gn,good),(True,'plain_natural',gp,good),(False,'natural_character',bn,bad),(False,'plain_natural',bp,bad)]):
                b['candidates'].append({'id':f'{h["id"]}-B{i}-C{j}','history_id':h['id'],'text':text,
                                         'intended':{'decision_id':d,'decision_correct':ok,'style':style},'observed':None})
        f['branches'].append(b)
        f['edges'].append({'source':f'hc::B{i}','target':f'hr::B{i}','kind':'preserve','allowed_pairs':[[good,good]],'justification':'相关条件相同，仅已结事项顺序变化。'})
    for h in ('hc','hr'):
        f['edges'].append({'source':h+'::B3','target':h+'::B5','kind':'change','allowed_pairs':[['reject','accept']],'justification':'从不适用公告变为已核验有效通告。'})
    return f

if __name__=='__main__':
    write_new(sys.argv[1] if len(sys.argv)>1 else 'smoke.jsonl',[fixture()])
