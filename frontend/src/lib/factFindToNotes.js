// JS port of services/fact_find.py::fact_find_to_notes — converts the structured
// (possibly hand-edited) fact-find object back into the plain-text notes format
// that POST /generate/report expects in its `notes` field. Keep in sync with the
// Python original; there is no backend endpoint that does this conversion.

export function factFindToNotes(data) {
  const lines = []

  const section = (title) => {
    lines.push('')
    lines.push('='.repeat(50))
    lines.push(title.toUpperCase())
    lines.push('='.repeat(50))
  }

  const field = (label, value) => {
    if (value !== undefined && value !== null && value !== '' && !(Array.isArray(value) && value.length === 0)) {
      lines.push(`${label}: ${value}`)
    }
  }

  const p = data.personal || {}
  section('Client Personal Details')
  field('Client 1', p.client1_name)
  field('Date of Birth', p.client1_dob)
  field('Client 2', p.client2_name)
  field('Date of Birth (2)', p.client2_dob)
  field('Address', p.address)
  field('Marital Status', p.marital_status)
  for (const d of p.dependants || []) {
    if (d.name) lines.push(`Dependant: ${d.name}, Age ${d.age || ''}, ${d.relationship || ''}`)
  }
  field('Client 1 Employment', p.client1_employment)
  field('Client 1 Employer', p.client1_employer)
  field('Client 2 Employment', p.client2_employment)
  field('Client 2 Employer', p.client2_employer)

  const inc = data.income || {}
  section('Income')
  field('Client 1 Gross Salary', inc.client1_gross_salary)
  field('Client 1 Net Monthly', inc.client1_net_monthly)
  field('Client 2 Gross Salary', inc.client2_gross_salary)
  field('Client 2 Net Monthly', inc.client2_net_monthly)
  field('Client 1 Bonus', inc.client1_bonus)
  field('Other Income', inc.other_income)
  field('Salary Sacrifice', inc.salary_sacrifice)
  field('Monthly Surplus', inc.monthly_surplus)

  const exp = data.expenditure || {}
  section('Expenditure')
  field('Mortgage/Rent Payment', exp.mortgage_payment)
  field('Total Monthly Expenditure', exp.total_monthly)
  field('Notes', exp.notes)

  const assets = data.assets || {}
  section('Assets & Savings')
  field('Property Value', assets.property_value)
  field('Mortgage Balance', assets.mortgage_balance)
  field('Property Equity', assets.property_equity)
  field('Premium Bonds', assets.premium_bonds)
  for (const acc of assets.cash_savings || []) {
    if (acc.value) lines.push(`Cash Savings: ${acc.provider || 'Unknown'} — ${acc.type || ''} — ${acc.value}`)
  }
  for (const isa of assets.isas || []) {
    if (isa.value) lines.push(`ISA: ${isa.provider || 'Unknown'} — ${isa.type || ''} — Value: ${isa.value} — Contributions: ${isa.contributions || ''}`)
  }
  for (const gia of assets.gia || []) {
    if (gia.value) lines.push(`GIA: ${gia.provider || 'Unknown'} — Value: ${gia.value}`)
  }

  section('Pensions')
  ;(data.pensions || []).forEach((pen, i) => {
    if (pen.provider || pen.current_value) {
      lines.push(
        `Pension ${i + 1}: ${pen.provider || 'Unknown'} | ${pen.type || ''} | Value: ${pen.current_value || ''} | ` +
        `Employee: ${pen.employee_contribution || ''} | Employer: ${pen.employer_contribution || ''} | ` +
        `Fund: ${pen.fund_name || ''} | Target age: ${pen.selected_retirement_age || ''} | ` +
        `Status: ${pen.status || ''} | ${pen.notes || ''}`
      )
    }
  })

  section('Protection')
  for (const pol of data.protection || []) {
    if (pol.type || pol.benefit) {
      lines.push(
        `Policy: ${pol.type || ''} | Provider: ${pol.provider || ''} | Benefit: ${pol.benefit || ''} | ` +
        `Premium: ${pol.premium || ''} | Term: ${pol.term || ''} | Basis: ${pol.basis || ''} | ${pol.notes || ''}`
      )
    }
  }

  const liab = data.liabilities || {}
  section('Liabilities')
  field('Mortgage Balance', liab.mortgage_balance)
  field('Mortgage Rate', liab.mortgage_rate)
  field('Mortgage Term', liab.mortgage_term)
  field('Mortgage Monthly', liab.mortgage_monthly)
  field('Other Loans', liab.other_loans)
  field('Credit Cards', liab.credit_cards)

  const obj = data.objectives || {}
  section('Objectives')
  field('Primary Objective', obj.primary_objective)
  field('Target Retirement Age (Client 1)', obj.target_retirement_age_client1)
  field('Target Retirement Age (Client 2)', obj.target_retirement_age_client2)
  field('Target Retirement Income', obj.target_retirement_income)
  field('Secondary Objectives', obj.secondary_objectives)
  field('Time Horizons', obj.time_horizons)
  field('Priorities', obj.priorities)
  field('Concerns', obj.concerns)

  const risk = data.risk || {}
  section('Attitude to Risk & Capacity for Loss')
  field('Questionnaire Tool', risk.questionnaire_tool)
  field('Score', risk.questionnaire_score)
  field('Profile Assigned', risk.profile_assigned)
  field('Capacity for Loss', risk.capacity_for_loss)
  field('Client Own Words', risk.client_own_words)
  field('Investment Time Horizon', risk.investment_time_horizon)

  const ep = data.estate_planning || {}
  section('Estate Planning')
  field('Will in Place', ep.will_in_place)
  field('Will Date', ep.will_date)
  field('LPA in Place', ep.lpa_in_place)
  field('IHT Position', ep.iht_position)
  field('Beneficiaries Noted', ep.beneficiaries_noted)
  field('Trust Arrangements', ep.trust_arrangements)

  const tax = data.tax || {}
  section('Tax Position')
  field('Client 1 Tax Band', tax.client1_tax_band)
  field('Client 2 Tax Band', tax.client2_tax_band)
  field('CGT Position', tax.cgt_position)
  field('Annual Allowance Used', tax.annual_allowance_used)
  field('ISA Allowance Used', tax.isa_allowance_used)
  field('Notes', tax.notes)

  return lines.join('\n')
}
