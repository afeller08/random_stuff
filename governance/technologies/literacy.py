import stripped.main as s

class Skill:
    pass


class Literacy(Skill):
    media = Tablet, Parchment, Paper, Digital


class Activity:
    pass


class ImpactableThing:
    traits = {}

    def permits(self, activity):
        return s.And(*[
            self.traits[req.name] >= req.thresh for req in activity.requirements
        ])

    def update(self, impact):
        for change in impact.traits:
            self.traits[change.name] += change.delta


class Person(ImpactableThing):
    def maybe_do(self, priority, locale):
        activity = locale.get_activity(priority, self)
        p_impact, l_impact, g_impact = s.If(
            s.And(self.permits(activity), locale.permits(activity)),
            self.perform(activity))
        self.update(p_impact)
        locale.update(l_impact)
        return g_impact

    def perform(self, activity):
        pass


def passive_thread(game, locale):
    for person in game[locale]:
        priority = person.get_priority()
        impact = person.maybe_do(priority, locale)
        game.update(impact)
