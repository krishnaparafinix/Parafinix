// Mirrors the 60-field JSON structure produced by POST /generate/extract
// (services/fact_find.py EXTRACTION_PROMPT on the backend).

export function emptyFactFind() {
  return {
    personal: {
      client1_name: '', client1_dob: '', client2_name: '', client2_dob: '',
      address: '', marital_status: '', dependants: [],
      client1_employment: '', client1_employer: '',
      client2_employment: '', client2_employer: '',
    },
    income: {
      client1_gross_salary: '', client1_net_monthly: '',
      client2_gross_salary: '', client2_net_monthly: '',
      client1_bonus: '', client2_bonus: '', other_income: '',
      salary_sacrifice: '', monthly_surplus: '',
    },
    expenditure: { mortgage_payment: '', total_monthly: '', notes: '' },
    assets: {
      cash_savings: [], isas: [], gia: [],
      property_value: '', mortgage_balance: '', property_equity: '', premium_bonds: '',
    },
    pensions: [],
    protection: [],
    liabilities: {
      mortgage_balance: '', mortgage_rate: '', mortgage_term: '', mortgage_monthly: '',
      other_loans: '', credit_cards: '', total_liabilities: '',
    },
    objectives: {
      primary_objective: '', target_retirement_age_client1: '', target_retirement_age_client2: '',
      target_retirement_income: '', secondary_objectives: '', time_horizons: '',
      priorities: '', concerns: '',
    },
    risk: {
      questionnaire_score: '', questionnaire_tool: '', profile_assigned: '',
      capacity_for_loss: '', client_own_words: '', investment_time_horizon: '',
    },
    estate_planning: {
      will_in_place: '', will_date: '', lpa_in_place: '', iht_position: '',
      beneficiaries_noted: '', trust_arrangements: '',
    },
    tax: {
      client1_tax_band: '', client2_tax_band: '', cgt_position: '',
      annual_allowance_used: '', isa_allowance_used: '', notes: '',
    },
    flags: [],
  }
}

// Fills any fields missing from a partially-extracted object with the empty schema
// so the review form never breaks on a shape mismatch from the AI.
export function normalizeFactFind(data) {
  const empty = emptyFactFind()
  if (!data || typeof data !== 'object') return empty
  const merged = { ...empty }
  for (const key of Object.keys(empty)) {
    if (Array.isArray(empty[key])) {
      merged[key] = Array.isArray(data[key]) ? data[key] : empty[key]
    } else {
      merged[key] = { ...empty[key], ...(data[key] || {}) }
    }
  }
  return merged
}

export const SIMPLE_SECTIONS = [
  {
    id: 'personal',
    title: 'Personal',
    fields: [
      ['client1_name', 'Client 1 name'],
      ['client1_dob', 'Client 1 date of birth'],
      ['client2_name', 'Client 2 name'],
      ['client2_dob', 'Client 2 date of birth'],
      ['address', 'Address'],
      ['marital_status', 'Marital status'],
      ['client1_employment', 'Client 1 employment'],
      ['client1_employer', 'Client 1 employer'],
      ['client2_employment', 'Client 2 employment'],
      ['client2_employer', 'Client 2 employer'],
    ],
  },
  {
    id: 'income',
    title: 'Income',
    fields: [
      ['client1_gross_salary', 'Client 1 gross salary'],
      ['client1_net_monthly', 'Client 1 net monthly'],
      ['client2_gross_salary', 'Client 2 gross salary'],
      ['client2_net_monthly', 'Client 2 net monthly'],
      ['client1_bonus', 'Client 1 bonus'],
      ['client2_bonus', 'Client 2 bonus'],
      ['other_income', 'Other income'],
      ['salary_sacrifice', 'Salary sacrifice'],
      ['monthly_surplus', 'Monthly surplus'],
    ],
  },
  {
    id: 'expenditure',
    title: 'Expenditure',
    fields: [
      ['mortgage_payment', 'Mortgage / rent payment'],
      ['total_monthly', 'Total monthly expenditure'],
      ['notes', 'Notes'],
    ],
  },
  {
    id: 'assets',
    title: 'Assets',
    fields: [
      ['property_value', 'Property value'],
      ['mortgage_balance', 'Mortgage balance'],
      ['property_equity', 'Property equity'],
      ['premium_bonds', 'Premium bonds'],
    ],
  },
  {
    id: 'liabilities',
    title: 'Liabilities',
    fields: [
      ['mortgage_balance', 'Mortgage balance'],
      ['mortgage_rate', 'Mortgage rate'],
      ['mortgage_term', 'Mortgage term'],
      ['mortgage_monthly', 'Mortgage monthly payment'],
      ['other_loans', 'Other loans'],
      ['credit_cards', 'Credit cards'],
      ['total_liabilities', 'Total liabilities'],
    ],
  },
  {
    id: 'objectives',
    title: 'Objectives',
    fields: [
      ['primary_objective', 'Primary objective'],
      ['target_retirement_age_client1', 'Target retirement age (client 1)'],
      ['target_retirement_age_client2', 'Target retirement age (client 2)'],
      ['target_retirement_income', 'Target retirement income'],
      ['secondary_objectives', 'Secondary objectives'],
      ['time_horizons', 'Time horizons'],
      ['priorities', 'Priorities'],
      ['concerns', 'Concerns'],
    ],
  },
  {
    id: 'risk',
    title: 'Risk',
    fields: [
      ['questionnaire_tool', 'Questionnaire tool'],
      ['questionnaire_score', 'Questionnaire score'],
      ['profile_assigned', 'Profile assigned'],
      ['capacity_for_loss', 'Capacity for loss'],
      ['client_own_words', "Client's own words"],
      ['investment_time_horizon', 'Investment time horizon'],
    ],
  },
  {
    id: 'estate_planning',
    title: 'Estate Planning',
    fields: [
      ['will_in_place', 'Will in place'],
      ['will_date', 'Will date'],
      ['lpa_in_place', 'LPA in place'],
      ['iht_position', 'IHT position'],
      ['beneficiaries_noted', 'Beneficiaries noted'],
      ['trust_arrangements', 'Trust arrangements'],
    ],
  },
  {
    id: 'tax',
    title: 'Tax',
    fields: [
      ['client1_tax_band', 'Client 1 tax band'],
      ['client2_tax_band', 'Client 2 tax band'],
      ['cgt_position', 'CGT position'],
      ['annual_allowance_used', 'Annual allowance used'],
      ['isa_allowance_used', 'ISA allowance used'],
      ['notes', 'Notes'],
    ],
  },
]

// Repeatable list fields, each keyed by [section, key] (section null = top-level array)
export const LIST_SECTIONS = [
  {
    section: 'personal', key: 'dependants', title: 'Dependants',
    fields: [['name', 'Name'], ['age', 'Age'], ['relationship', 'Relationship']],
  },
  {
    section: 'assets', key: 'cash_savings', title: 'Cash Savings',
    fields: [['provider', 'Provider'], ['type', 'Type'], ['value', 'Value']],
  },
  {
    section: 'assets', key: 'isas', title: 'ISAs',
    fields: [['provider', 'Provider'], ['type', 'Type'], ['value', 'Value'], ['contributions', 'Contributions']],
  },
  {
    section: 'assets', key: 'gia', title: 'General Investment Accounts',
    fields: [['provider', 'Provider'], ['value', 'Value']],
  },
  {
    section: null, key: 'pensions', title: 'Pensions',
    fields: [
      ['provider', 'Provider'], ['type', 'Type'], ['current_value', 'Current value'],
      ['employee_contribution', 'Employee contribution'], ['employer_contribution', 'Employer contribution'],
      ['fund_name', 'Fund name'], ['selected_retirement_age', 'Selected retirement age'],
      ['status', 'Status'], ['notes', 'Notes'],
    ],
  },
  {
    section: null, key: 'protection', title: 'Protection',
    fields: [
      ['type', 'Type'], ['provider', 'Provider'], ['benefit', 'Benefit'],
      ['premium', 'Premium'], ['term', 'Term'], ['basis', 'Basis'], ['notes', 'Notes'],
    ],
  },
]
