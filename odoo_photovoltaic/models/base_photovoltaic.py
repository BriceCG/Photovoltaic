from odoo import api, fields, models
import math


class BasePhotovoltaic(models.Model):
    _name = 'base.photovoltaic'

    name = fields.Char(string="Nom", default=lambda self: self.get_default_name())

    n_ond = fields.Float(string="N Ond")
    ej = fields.Integer(string="Ej", compute='_compute_ej', store=True)

    ei = fields.Float(string="Ensoleillement du lieu (Ei)")
    k = fields.Float(string="Coefficient de pertes (K)")
    pu = fields.Float(string="Pu")
    pc = fields.Float(string="Puissance crête (PC)", compute='_compute_pc', store=True)
    np = fields.Float(string="Nombre de panneau (np)", compute='_compute_np', store=True)

    us = fields.Float(string="Tension du système (us)", compute='_compute_us', store=True)
    cu = fields.Float(string="cu")
    kd = fields.Float(string="Coefficient de profondeur (kd)")
    nj = fields.Float(string="Nombre de jour d'autonomie (nj)")
    ct = fields.Float(string="ct", compute='_compute_ct', store=True)
    tb = fields.Float(string="Tb")

    branch_number = fields.Float(string="Nombre de branche", compute='_compute_branch_number', store=True)
    battery_number = fields.Float(string="Nombre de batterie", compute='_compute_battery_number', store=True)

    regulator_tension = fields.Float(string="Tension du regulateur", compute='_compute_regulator_tension', store=True)
    photovoltaic_line_ids = fields.One2many('base.photovoltaic.line', 'base_photovoltaic_id')

    def get_default_name(self):
        date = fields.Date.today().strftime('%d/%m/%Y')
        name = 'Consommation du ' + date
        return name

    @api.onchange('n_ond')
    def change_n_ond(self):
        for rec in self:
            if len(rec.photovoltaic_line_ids) > 0:
                for photovoltaic_line in rec.photovoltaic_line_ids:
                    photovoltaic_line.n_ond = rec.n_ond

    @api.depends('photovoltaic_line_ids')
    def _compute_ej(self):
        for rec in self:
            if len(rec.photovoltaic_line_ids) > 0:
                rec.ej = sum(rec.photovoltaic_line_ids.mapped('total_consumption_line'))
            else:
                rec.ej = 0

    @api.depends('ej', 'k', 'ei')
    def _compute_pc(self):
        for rec in self:
            if rec.k > 0 and rec.ei > 0:
                rec.pc = rec.ej / (rec.k * rec.ei)

            else:
                rec.pc = 0

    @api.depends('pu', 'pc')
    def _compute_np(self):
        for rec in self:
            if rec.pu > 0:
                rec.np = math.ceil(rec.pc / rec.pu)
            else:
                rec.np = 0

    @api.depends('photovoltaic_line_ids')
    def _compute_us(self):
        for rec in self:
            if len(rec.photovoltaic_line_ids):
                total_ni_pi_ci = sum([photovoltaic_line.number * photovoltaic_line.power * photovoltaic_line.ci for photovoltaic_line in rec.photovoltaic_line_ids])
                if total_ni_pi_ci <= 200:
                    rec.us = 12
                elif 200 < total_ni_pi_ci <= 2000:
                    rec.us = 24
                elif 2000 < total_ni_pi_ci <= 5000:
                    rec.us = 48
                else:
                    rec.us = 0
            else:
                rec.us = 0

    @api.depends('ej', 'nj', 'kd', 'us')
    def _compute_ct(self):
        for rec in self:
            if rec.kd > 0 and rec.us > 0:
                rec.ct = (rec.ej * rec.nj) / (rec.kd * rec.us)

    @api.depends('ct', 'cu')
    def _compute_branch_number(self):
        for rec in self:
            if rec.cu > 0:
                rec.branch_number = rec.ct / rec.cu
            else:
                rec.branch_number = 0

    @api.depends('branch_number', 'us', 'tb')
    def _compute_battery_number(self):
        for rec in self:
            if rec.tb:
                rec.battery_number = (rec.us / rec.tb) * rec.branch_number
            else:
                rec.battery_number = 0

    @api.depends('us', 'photovoltaic_line_ids')
    def _compute_regulator_tension(self):
        for rec in self:
            if len(rec.photovoltaic_line_ids) > 0:
                total_ni_pi = sum([photovoltaic_line.number * photovoltaic_line.power for photovoltaic_line in rec.photovoltaic_line_ids])
                u_min = 11.4 * (rec.us / 12)
                regulator_tension = total_ni_pi / u_min if u_min > 0 else 0
                regulator_tension = math.ceil(regulator_tension / 5) * 5
                rec.regulator_tension = regulator_tension
            else:
                rec.regulator_tension = 0

    def round_up(self, n, decimals=0):
        multiplier = 10 ** decimals
        return math.ceil(n * multiplier) / multiplier