JanSathi schemes.json — 50 scheme/service records
============================================================

INSTALL
Replace your project's existing data/schemes.json with this file. Keep it as a JSON array.
The fields expected by the existing matcher are present: name, summary, verified, official_url,
occupations, states, min_age and max_age. Extra fields provide benefits, eligibility, documents,
application steps, keywords, source type, review date and cautions.

ACCURACY NOTES
- `verified: true` means the record is grounded in an official government portal/listing. It does NOT
  mean every scheme detail was independently verified against a current Government Resolution, that
  applications are open today, or that a user is eligible.
- Several entries are official directories or pointers to a family of schemes rather than a single
  benefit. Their status_note explains this.
- Amounts, deadlines, eligibility, beneficiary lists, documents and active components can change.
  JanSathi should share a concise summary, mention that eligibility is not guaranteed, and link to
  the official page instead of promising a payment.
- Source pages used include PM-KISAN (https://www.pmkisan.gov.in/), Maharashtra MahaDBT
  (https://mahadbt.maharashtra.gov.in/), Maharashtra Ladki Bahin
  (https://ladakibahin.maharashtra.gov.in/), National Scholarship Portal
  (https://scholarships.gov.in/), PMAY-U (https://pmay-urban.gov.in/), PM-JAY
  (https://pmjay.gov.in/) and other official scheme portals.
- Last source review date recorded in this dataset: 2026-10-24.

FARMER IN MUMBAI EXAMPLE
Ask whether the person's farmland is in Maharashtra and which district; a person can live in Mumbai
while farming land elsewhere. Then show 2–4 relevant records (for example PM-KISAN, Namo Shetkari,
PMFBY, and a matching MahaDBT component). Don't read the entire database aloud. Ask about land
records, crop, Farmer ID, category where relevant, and whether they want application steps.

Important: This is a hackathon starter dataset. Before production use, review the current Government
Resolutions and official scheme pages, and add a repeatable source-update process.
