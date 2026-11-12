"""v2 scenes: convenience is counterbalanced against the attitude pole.

Each family gets a neutral scene that names both options without saying which is
easier, plus two cost sentences:
  cost_pos: the pos-pole option is the costly/slow one (neg pole is convenient)
  cost_neg: the neg-pole option is the costly/slow one (pos pole is convenient; this is v1's arrangement)
Attitudes, experiences and K questions are reused from families.py.
"""

V2 = {
    "T01_merchant": dict(
        scene="The travelling merchant Oswin offers {role} a crate of dyes, to be paid now and delivered by Oswin tomorrow. A dye seller at the market in the next town has the same dyes.",
        opt_pos="Buy the dyes from Oswin.", opt_neg="Buy the dyes from the seller in the next town.",
        cost_pos="Oswin charges four silver more than the market seller, and the next town is only a short walk away.",
        cost_neg="The next town is a full day's walk away, and the market seller charges four silver more than Oswin."),
    "T02_healer": dict(
        scene="{role}'s young son has had a bad cough for a week. {role} can have him treated by the healer Ilse or by the city physician.",
        opt_pos="Have Ilse treat the boy.", opt_neg="Have the city physician treat the boy.",
        cost_pos="Ilse lives two days away in the hills, while the city physician is visiting the village today.",
        cost_neg="Ilse can come today, while the city physician is two days' journey away."),
    "T03_captain": dict(
        scene="{role} has found clear evidence that a neighbour is smuggling stolen goods. {role} can give it to the guard captain Varo or to the magistrate's office.",
        opt_pos="Give the evidence to Varo.", opt_neg="Give the evidence to the magistrate's office.",
        cost_pos="Varo is away for a month, while a clerk from the magistrate's office is in the village today.",
        cost_neg="Varo is in the village today, while the magistrate's office is a month away by courier."),
    "T04_loan": dict(
        scene="The farmer Pell asks {role} to lend him fifteen silver until the harvest, promising to repay it in the autumn.",
        opt_pos="Lend Pell the fifteen silver.", opt_neg="Politely refuse the loan.",
        cost_pos="{role} had saved exactly that sum to buy a much-needed winter coat this week.",
        cost_neg="{role} has plenty of spare savings and no plans for the money."),
    "T05_smith": dict(
        scene="{role} needs a new axe and can order it from the blacksmith Dorn or from a smith in the next valley, for the same price.",
        opt_pos="Order the axe from Dorn.", opt_neg="Order the axe from the smith in the next valley.",
        cost_pos="Dorn is fully booked and needs three weeks, while the other smith can make it this week.",
        cost_neg="Dorn can make it this week, while the other smith needs three weeks."),
    "T06_secret": dict(
        scene="{role}'s pottery business is close to failing, and {role} wants advice without the rest of the village finding out. {role} can confide in the neighbour Tamsin or in an old teacher.",
        opt_pos="Confide in Tamsin.", opt_neg="Confide in the old teacher.",
        cost_pos="Tamsin is away for two weeks, while the old teacher is visiting Ashford tonight.",
        cost_neg="Tamsin can listen tonight, while the old teacher lives far away and would only reply by letter in a few weeks."),
    "T07_guide": dict(
        scene="{role} must cross the mountain pass and can hire the guide Rook or another guide.",
        opt_pos="Hire Rook.", opt_neg="Hire the other guide.",
        cost_pos="Rook charges twice as much and can only start in two weeks; the other guide can start tomorrow.",
        cost_neg="The other guide charges twice as much and can only start in two weeks; Rook can start tomorrow."),
    "T08_innkeeper": dict(
        scene="{role} is leaving for a week-long journey with a purse of savings. The innkeeper Bess offers to keep it in her strongbox; otherwise {role} will carry it along.",
        opt_pos="Leave the purse with Bess.", opt_neg="Carry the purse along on the journey.",
        cost_pos="Bess's inn is in the opposite direction, so leaving the purse there adds half a day to the journey, and the road ahead is known to be safe.",
        cost_neg="The inn is on the way, and the road ahead is known for pickpockets."),
    "T09_scholar": dict(
        scene="The scholar Aldric advises {role} to sell this year's grain now instead of storing it to sell in winter.",
        opt_pos="Sell the grain now, as Aldric advises.", opt_neg="Store the grain and sell it in winter.",
        cost_pos="Selling now means hauling the grain to a distant market this week, while {role}'s barn has plenty of room to store it.",
        cost_neg="{role}'s barn is leaking and storing the grain would mean repairing it first, while a buyer can collect the grain tomorrow."),
    "T10_cousin": dict(
        scene="{role} needs help moving the household to a new cottage on Saturday and can ask cousin Mira or hire labourers.",
        opt_pos="Ask cousin Mira to help.", opt_neg="Hire labourers.",
        cost_pos="Mira lives a day's ride away, while labourers can be hired cheaply at the market next door.",
        cost_neg="Mira lives next door, while labourers would cost a week's earnings."),
    "T11_captain_ship": dict(
        scene="{role} must ship this year's wool to the southern market, either with the ship captain Hale or with another ship.",
        opt_pos="Ship the wool with Captain Hale.", opt_neg="Ship the wool with the other ship.",
        cost_pos="Hale's ship leaves in two weeks and charges more; the other ship leaves tomorrow.",
        cost_neg="Hale's ship leaves tomorrow; the other ship leaves in two weeks and charges more."),
    "T12_apprentice": dict(
        scene="{role} must travel to a funeral for three days and can either leave the apprentice Finn in charge of the shop or close it.",
        opt_pos="Leave Finn in charge of the shop.", opt_neg="Close the shop for the three days.",
        cost_pos="These are the quietest days of the year, so closing the shop would lose almost nothing.",
        cost_neg="These are the busiest market days of the year, so closing the shop would lose a month's takings."),
    "P01_water": dict(
        scene="{role} needs to reach the market town and can cross the Grey River by ferry or go round by the bridge road.",
        opt_pos="Take the ferry across the river.", opt_neg="Take the bridge road.",
        cost_pos="Today the ferry is crowded and slow and would take longer than the bridge road.",
        cost_neg="The ferry takes an hour, while the bridge road takes most of the day."),
    "P02_heights": dict(
        scene="{role} is walking home and can take the old cliff stairs, steep and without a railing, or the valley path.",
        opt_pos="Climb the old cliff stairs.", opt_neg="Take the valley path.",
        cost_pos="A recent landslide has made the cliff stairs the longer way today.",
        cost_neg="The cliff stairs would save an hour."),
    "P03_dogs": dict(
        scene="{role} is going to the well. One way runs past a farmyard where a large dog is kept on a long chain; the other way goes round the fields.",
        opt_pos="Take the way past the farmyard dog.", opt_neg="Take the way round the fields.",
        cost_pos="The way past the farmyard is muddy today and takes longer.",
        cost_neg="The way past the farmyard is half as long."),
    "P04_venture": dict(
        scene="A merchant invites {role} to put half of {role}'s savings into a cargo of spices. If the voyage succeeds the stake triples; if the ship is lost, so is the money.",
        opt_pos="Invest half the savings in the spice cargo.", opt_neg="Decline the offer.",
        cost_pos="To invest, {role} would have to travel to the port this week to sign the papers.",
        cost_neg="Declining would mean telling the merchant, an old friend, to his face in front of the guild."),
    "P05_forest": dict(
        scene="{role} is late returning home and can take the path through the Blackwood or the high road.",
        opt_pos="Take the path through the Blackwood.", opt_neg="Take the high road.",
        cost_pos="Tonight a fallen tree blocks part of the Blackwood path, making it slower than the high road.",
        cost_neg="The Blackwood path takes one hour; the high road takes three."),
    "P06_debt": dict(
        scene="{role} wants a second loom and can borrow forty silver from the moneylender or keep saving for it.",
        opt_pos="Borrow the forty silver.", opt_neg="Keep saving for the loom.",
        cost_pos="The moneylender lives in the city, three days away, and requires a guarantor; {role} could save the money in a few months.",
        cost_neg="The moneylender is next door; saving would take two years."),
    "P07_capital": dict(
        scene="{role} is offered a clerk's post in the capital and can also stay in the clerk's post in the village.",
        opt_pos="Accept the post in the capital.", opt_neg="Stay in the village post.",
        cost_pos="The capital post pays the same as the village post, and moving would cost most of {role}'s savings.",
        cost_neg="The capital post pays three times as much, and the move would be paid for."),
    "P08_horses": dict(
        scene="{role} must carry a letter to the next town and can borrow a lively young horse or walk.",
        opt_pos="Borrow the horse and ride.", opt_neg="Walk to the next town.",
        cost_pos="The horse is stabled on the far side of the village, and the letter is not urgent.",
        cost_neg="The letter is urgent, and riding would arrive by noon instead of evening."),
    "P09_mushrooms": dict(
        scene="A neighbour offers {role} a basket of wild mushrooms from the forest for supper. Otherwise supper is plain bread and cheese.",
        opt_pos="Cook the wild mushrooms for supper.", opt_neg="Have bread and cheese instead.",
        cost_pos="The mushrooms would need an hour of cleaning and cooking, and the bread and cheese are already on the table.",
        cost_neg="The bread is stale and the cheese has gone mouldy; the mushrooms are already cleaned."),
    "P10_speech": dict(
        scene="The village needs someone to present its petition to the lord in front of the assembled court. {role} can volunteer to speak, or the reeve can speak instead.",
        opt_pos="Volunteer to present the petition.", opt_neg="Let the reeve speak instead.",
        cost_pos="The reeve knows the petition well and has already offered to speak.",
        cost_neg="The reeve is ill and barely knows the petition, which {role} wrote."),
    "P11_bees": dict(
        scene="A neighbour offers to settle a debt with {role} either with two beehives or with a sack of flour.",
        opt_pos="Take the two beehives.", opt_neg="Take the sack of flour.",
        cost_pos="The flour is worth more, and {role} is short of flour for the winter.",
        cost_neg="The beehives are worth twice as much as the flour."),
    "P12_stranger": dict(
        scene="On a rainy night, a stranger knocks at {role}'s door asking for shelter until morning.",
        opt_pos="Let the stranger in for the night.", opt_neg="Point the stranger to the inn.",
        cost_pos="The inn is just next door and has empty rooms.",
        cost_neg="The inn is two miles away down a flooded road."),
}
