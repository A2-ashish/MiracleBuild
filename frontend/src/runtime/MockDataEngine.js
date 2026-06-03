// Mock Data Engine
// Generates realistic mock data based on column definitions

const FIRST_NAMES = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace', 'Henry', 'Ivy', 'Jack']
const LAST_NAMES = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Wilson', 'Taylor']
const COMPANIES = ['Acme Corp', 'TechFlow', 'DataPrime', 'CloudSync', 'NetWave', 'InnoSoft', 'BrightAI', 'Quantum Ltd']
const STATUSES = ['active', 'inactive', 'pending', 'completed', 'cancelled']
const EMAILS_DOMAINS = ['gmail.com', 'outlook.com', 'company.com', 'business.org']
const CITIES = ['New York', 'San Francisco', 'London', 'Tokyo', 'Berlin', 'Sydney', 'Toronto', 'Paris']
const PRIORITIES = ['low', 'medium', 'high', 'critical']
const CATEGORIES = ['General', 'Sales', 'Support', 'Engineering', 'Marketing', 'Finance']

function randomItem(arr) {
  return arr[Math.floor(Math.random() * arr.length)]
}

function randomDate(daysBack = 365) {
  const d = new Date()
  d.setDate(d.getDate() - Math.floor(Math.random() * daysBack))
  return d.toISOString().split('T')[0]
}

function randomId() {
  return Math.floor(Math.random() * 9000) + 1000
}

function generateValueForColumn(col) {
  const key = (col.key || col.name || '').toLowerCase()
  const type = (col.type || 'text').toLowerCase()

  // ID fields
  if (key === 'id' || key.endsWith('_id')) {
    return randomId()
  }

  // Name fields
  if (key === 'name' || key === 'full_name' || key === 'fullname') {
    return `${randomItem(FIRST_NAMES)} ${randomItem(LAST_NAMES)}`
  }
  if (key === 'first_name' || key === 'firstname') {
    return randomItem(FIRST_NAMES)
  }
  if (key === 'last_name' || key === 'lastname') {
    return randomItem(LAST_NAMES)
  }

  // Email
  if (key === 'email' || key.includes('email') || type === 'email') {
    const first = randomItem(FIRST_NAMES).toLowerCase()
    return `${first}@${randomItem(EMAILS_DOMAINS)}`
  }

  // Phone
  if (key === 'phone' || key.includes('phone') || key.includes('tel')) {
    return `+1 (${Math.floor(Math.random() * 900) + 100}) ${Math.floor(Math.random() * 900) + 100}-${Math.floor(Math.random() * 9000) + 1000}`
  }

  // Status
  if (key === 'status' || key.includes('status') || type === 'badge') {
    return randomItem(STATUSES)
  }

  // Priority
  if (key === 'priority' || key.includes('priority')) {
    return randomItem(PRIORITIES)
  }

  // Category
  if (key === 'category' || key.includes('category') || key === 'type') {
    return randomItem(CATEGORIES)
  }

  // Company
  if (key === 'company' || key.includes('company') || key === 'organization') {
    return randomItem(COMPANIES)
  }

  // City/Location
  if (key === 'city' || key === 'location' || key.includes('city')) {
    return randomItem(CITIES)
  }

  // Date fields
  if (key.includes('date') || key.includes('created') || key.includes('updated') || type === 'date') {
    return randomDate()
  }

  // Price/Amount
  if (key.includes('price') || key.includes('amount') || key.includes('cost') || key.includes('revenue') || key.includes('salary')) {
    return `$${(Math.random() * 10000 + 100).toFixed(2)}`
  }

  // Count/Number
  if (type === 'number' || key.includes('count') || key.includes('quantity') || key.includes('age')) {
    return Math.floor(Math.random() * 100) + 1
  }

  // Boolean
  if (type === 'boolean' || key.includes('is_') || key.includes('has_')) {
    return Math.random() > 0.5 ? 'Yes' : 'No'
  }

  // Title
  if (key === 'title' || key === 'subject') {
    const prefixes = ['New', 'Updated', 'Review', 'Draft', 'Final']
    const nouns = ['Report', 'Proposal', 'Document', 'Analysis', 'Plan']
    return `${randomItem(prefixes)} ${randomItem(nouns)}`
  }

  // Description
  if (key === 'description' || key === 'notes' || key === 'bio') {
    return 'Lorem ipsum dolor sit amet...'
  }

  // URL/Link
  if (key === 'url' || key === 'website' || key.includes('link')) {
    return `https://example.com/${Math.random().toString(36).substring(7)}`
  }

  // Role
  if (key === 'role' || key.includes('role')) {
    return randomItem(['Admin', 'User', 'Manager', 'Editor', 'Viewer'])
  }

  // Default: generic text
  return `${key}_${randomId()}`
}

export function generateMockData(columns, rowCount = 5) {
  const rows = []
  for (let i = 0; i < rowCount; i++) {
    const row = {}
    for (const col of columns) {
      const key = col.key || col.name || `col_${i}`
      row[key] = generateValueForColumn(col)
    }
    rows.push(row)
  }
  return rows
}
