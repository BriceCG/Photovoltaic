from odoo import api, fields, models

base_ci = [
    {
        'number': [2],
        'ci_value': 0.85
    },
    {
        'number': [3],
        'ci_value': 0.8
    },
    {
        'number': [4, 8],
        'ci_value': 0.75
    },
    {
        'number': [6, 7],
        'ci_value': 0.7
    },
    {
        'number': [8, 10],
        'ci_value': 0.65
    },
    {
        'number': [11, 15],
        'ci_value': 0.6
    },
    {
        'number': [16, 20],
        'ci_value': 0.55
    },
    {
        'number': [21, 30],
        'ci_value': 0.5
    },
    {
        'number': [31, 50],
        'ci_value': 0.45
    },
    {
        'number': [51, 150],
        'ci_value': 0.4
    },
    {
        'number': [151, 1000],
        'ci_value': 0.35,
    },
]


class BasePhotovoltaicLine(models.Model):
    _name = 'base.photovoltaic.line'

    name = fields.Char(string="Designation")
    number = fields.Integer(string="Nombre")
    power = fields.Float(string="Puissance")
    working_hours = fields.Float(string="Heure de marche")
    ci = fields.Float(string="ci", compute='_compute_ci', store=True)
    total_consumption_line = fields.Float(string="Consommation", compute='_compute_total_consumption_line', store=True)

    n_ond = fields.Float(string="N Ond")
    is_onduleur = fields.Boolean(string="Onduleur", default=False)
    base_photovoltaic_id = fields.Many2one('base.photovoltaic')

    @api.depends('number')
    def _compute_ci(self):
        for rec in self:
            if rec.number:
                rec.ci = rec.get_ci(rec.number)
            else:
                rec.ci = 0

    @api.depends('number', 'power', 'working_hours', 'ci', 'is_onduleur')
    def _compute_total_consumption_line(self):
        for rec in self:
            total = rec.number * rec.power * rec.working_hours * rec.ci
            if not rec.is_onduleur:
                rec.total_consumption_line = total
            else:
                rec.total_consumption_line = total / rec.n_ond

    def get_ci(self, number):
        ci_value = 1
        for ci in base_ci:
            if len(ci['number']) == 1:
                if ci['number'][0] == number:
                    ci_value = ci['ci_value']

            if len(ci['number']) > 1:
                if ci['number'][0] <= number <= ci['number'][-1]:
                    ci_value = ci['ci_value']

        return ci_value




