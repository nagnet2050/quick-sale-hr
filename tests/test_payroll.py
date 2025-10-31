import unittest
from app import create_app
from app.models.payroll import Payroll


class PayrollComputeNetTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        # set deterministic payroll config for tests
        self.app.config['PAYROLL_TAX_RATE'] = 0.10
        self.app.config['PAYROLL_INSURANCE_RATE'] = 0.02
        self.app.config['PAYROLL_TAX_EXEMPT_LIMIT'] = 0.0
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_compute_net_basic_tax_and_insurance(self):
        # basic + allowances = 1000 + 100 = 1100 taxable
        p = Payroll(basic=1000.0, allowances=100.0, bonus=0.0, overtime=0.0, deductions=0.0)
        breakdown = p.compute_net()
        # tax = 110 (10% of 1100)
        self.assertAlmostEqual(breakdown['tax'], 110.0)
        # insurance = 22 (2% of basic+allowances)
        self.assertAlmostEqual(breakdown['insurance'], 22.0)
        # net = gross - tax - insurance
        self.assertAlmostEqual(breakdown['net'], 968.0)

    def test_tax_exempt_limit_applies(self):
        # set a high exempt limit -> no tax
        self.app.config['PAYROLL_TAX_EXEMPT_LIMIT'] = 2000.0
        p = Payroll(basic=1000.0, allowances=100.0, bonus=0.0, overtime=0.0, deductions=0.0)
        breakdown = p.compute_net()
        self.assertAlmostEqual(breakdown['tax'], 0.0)
        # insurance still applies
        self.assertAlmostEqual(breakdown['insurance'], 22.0)


if __name__ == '__main__':
    unittest.main()
