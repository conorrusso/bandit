"""
Bandit Known Vendor Library
============================
Curated list of common vendors mapped to their function categories.
Top vendors per category based on real-world GRC assessment programs.

Contributing: open a PR to add vendors.
Format: "vendor-slug": [VendorFunction.CATEGORY, ...]

Slug rules:
  - lowercase
  - hyphens not underscores
  - no legal suffixes (inc, ltd, corp, llc)
  - no extensions (.com, .ai, .io)
  - no generic words (technologies, solutions, software)
"""

from core.profiles.vendor_functions import VendorFunction as V

KNOWN_VENDORS: dict[str, list] = {

    # ─────────────────────────────────────────────────────────────
    # FINANCIAL PROCESSING
    # AP/AR, procurement, expense, billing, payroll, ERP
    # Triggers: SOC 1 Type II, SOX if public company
    # ─────────────────────────────────────────────────────────────
    "netsuite":           [V.FINANCIAL_PROCESSING, V.HR_PEOPLE],
    "quickbooks":         [V.FINANCIAL_PROCESSING],
    "xero":               [V.FINANCIAL_PROCESSING],
    "sage":               [V.FINANCIAL_PROCESSING, V.HR_PEOPLE],
    "freshbooks":         [V.FINANCIAL_PROCESSING],
    "wave":               [V.FINANCIAL_PROCESSING],
    "ramp":               [V.FINANCIAL_PROCESSING, V.PAYMENTS],
    "brex":               [V.FINANCIAL_PROCESSING, V.PAYMENTS],
    "zip":                [V.FINANCIAL_PROCESSING],
    "coupa":              [V.FINANCIAL_PROCESSING],
    "concur":             [V.FINANCIAL_PROCESSING],
    "expensify":          [V.FINANCIAL_PROCESSING],
    "bill":               [V.FINANCIAL_PROCESSING],
    "tipalti":            [V.FINANCIAL_PROCESSING, V.PAYMENTS],
    "airbase":            [V.FINANCIAL_PROCESSING],
    "sap":                [V.FINANCIAL_PROCESSING, V.HR_PEOPLE, V.SUPPLY_CHAIN],
    "oracle":             [V.FINANCIAL_PROCESSING, V.HR_PEOPLE, V.INFRASTRUCTURE],
    "microsoft-dynamics": [V.FINANCIAL_PROCESSING, V.HR_PEOPLE, V.CUSTOMER_DATA],
    "anaplan":            [V.FINANCIAL_PROCESSING, V.ANALYTICS_BI],
    "workiva":            [V.FINANCIAL_PROCESSING, V.LEGAL_COMPLIANCE],
    "blackline":          [V.FINANCIAL_PROCESSING],
    "tradeshift":         [V.FINANCIAL_PROCESSING, V.SUPPLY_CHAIN],
    "procurify":          [V.FINANCIAL_PROCESSING],
    "teampay":            [V.FINANCIAL_PROCESSING],
    "floqast":            [V.FINANCIAL_PROCESSING],
    "planful":            [V.FINANCIAL_PROCESSING, V.ANALYTICS_BI],

    # ─────────────────────────────────────────────────────────────
    # HR & PEOPLE
    # HRIS, payroll, benefits, recruiting, performance, L&D
    # Triggers: Employee data, benefits may include health data
    # ─────────────────────────────────────────────────────────────
    "workday":            [V.HR_PEOPLE, V.FINANCIAL_PROCESSING, V.ANALYTICS_BI],
    "adp":                [V.HR_PEOPLE, V.FINANCIAL_PROCESSING],
    "rippling":           [V.HR_PEOPLE, V.FINANCIAL_PROCESSING, V.IDENTITY_ACCESS],
    "bamboohr":           [V.HR_PEOPLE],
    "gusto":              [V.HR_PEOPLE, V.FINANCIAL_PROCESSING],
    "paychex":            [V.HR_PEOPLE, V.FINANCIAL_PROCESSING],
    "paylocity":          [V.HR_PEOPLE, V.FINANCIAL_PROCESSING],
    "ceridian":           [V.HR_PEOPLE, V.FINANCIAL_PROCESSING],
    "ukg":                [V.HR_PEOPLE, V.FINANCIAL_PROCESSING],
    "greenhouse":         [V.HR_PEOPLE],
    "lever":              [V.HR_PEOPLE],
    "workable":           [V.HR_PEOPLE],
    "ashby":              [V.HR_PEOPLE],
    "lattice":            [V.HR_PEOPLE],
    "culture-amp":        [V.HR_PEOPLE],
    "15five":             [V.HR_PEOPLE],
    "betterworks":        [V.HR_PEOPLE],
    "deel":               [V.HR_PEOPLE, V.FINANCIAL_PROCESSING],
    "remote":             [V.HR_PEOPLE, V.FINANCIAL_PROCESSING],
    "oyster":             [V.HR_PEOPLE, V.FINANCIAL_PROCESSING],
    "learnupon":          [V.HR_PEOPLE],
    "docebo":             [V.HR_PEOPLE],
    "cornerstone":        [V.HR_PEOPLE],
    "bswift":             [V.HR_PEOPLE],
    "benefitfocus":       [V.HR_PEOPLE],
    "darwin":             [V.HR_PEOPLE],
    "personio":           [V.HR_PEOPLE],
    "hibob":              [V.HR_PEOPLE],
    "namely":             [V.HR_PEOPLE, V.FINANCIAL_PROCESSING],

    # ─────────────────────────────────────────────────────────────
    # CUSTOMER DATA
    # CRM, support, marketing automation, success
    # Triggers: Customer PII at scale, DPA critical
    # ─────────────────────────────────────────────────────────────
    "salesforce":         [V.CUSTOMER_DATA, V.ANALYTICS_BI],
    "hubspot":            [V.CUSTOMER_DATA, V.ANALYTICS_BI],
    "zendesk":            [V.CUSTOMER_DATA],
    "intercom":           [V.CUSTOMER_DATA],
    "freshdesk":          [V.CUSTOMER_DATA],
    "servicenow":         [V.CUSTOMER_DATA, V.LEGAL_COMPLIANCE],
    "pipedrive":          [V.CUSTOMER_DATA],
    "zoho":               [V.CUSTOMER_DATA, V.FINANCIAL_PROCESSING],
    "close":              [V.CUSTOMER_DATA],
    "outreach":           [V.CUSTOMER_DATA],
    "salesloft":          [V.CUSTOMER_DATA],
    "apollo":             [V.CUSTOMER_DATA],
    "marketo":            [V.CUSTOMER_DATA, V.ANALYTICS_BI],
    "mailchimp":          [V.CUSTOMER_DATA],
    "klaviyo":            [V.CUSTOMER_DATA],
    "braze":              [V.CUSTOMER_DATA, V.ANALYTICS_BI],
    "iterable":           [V.CUSTOMER_DATA],
    "gainsight":          [V.CUSTOMER_DATA],
    "totango":            [V.CUSTOMER_DATA],
    "churnzero":          [V.CUSTOMER_DATA],
    "gong":               [V.CUSTOMER_DATA, V.AI_ML],
    "chorus":             [V.CUSTOMER_DATA, V.AI_ML],
    "drift":              [V.CUSTOMER_DATA, V.AI_ML],
    "front":              [V.CUSTOMER_DATA],
    "kustomer":           [V.CUSTOMER_DATA],
    "gladly":             [V.CUSTOMER_DATA],
    "liveagent":          [V.CUSTOMER_DATA],

    # ─────────────────────────────────────────────────────────────
    # INFRASTRUCTURE & CLOUD
    # IaaS, PaaS, CDN, DNS, hosting, databases
    # Note: shared responsibility model applies to all
    # ─────────────────────────────────────────────────────────────
    "aws":                [V.INFRASTRUCTURE],
    "azure":              [V.INFRASTRUCTURE],
    "gcp":                [V.INFRASTRUCTURE],
    "cloudflare":         [V.INFRASTRUCTURE],
    "fastly":             [V.INFRASTRUCTURE],
    "akamai":             [V.INFRASTRUCTURE],
    "heroku":             [V.INFRASTRUCTURE],
    "digitalocean":       [V.INFRASTRUCTURE],
    "linode":             [V.INFRASTRUCTURE],
    "vultr":              [V.INFRASTRUCTURE],
    "vercel":             [V.INFRASTRUCTURE],
    "netlify":            [V.INFRASTRUCTURE],
    "render":             [V.INFRASTRUCTURE],
    "railway":            [V.INFRASTRUCTURE],
    "mongodb":            [V.INFRASTRUCTURE],
    "planetscale":        [V.INFRASTRUCTURE],
    "supabase":           [V.INFRASTRUCTURE],
    "neon":               [V.INFRASTRUCTURE],
    "twilio":             [V.INFRASTRUCTURE, V.COMMUNICATION],
    "sendgrid":           [V.INFRASTRUCTURE, V.COMMUNICATION],
    "mailgun":            [V.INFRASTRUCTURE, V.COMMUNICATION],
    "datadog":            [V.INFRASTRUCTURE, V.SECURITY_TOOLING],
    "newrelic":           [V.INFRASTRUCTURE, V.SECURITY_TOOLING],
    "pagerduty":          [V.INFRASTRUCTURE],
    "elastic":            [V.INFRASTRUCTURE, V.SECURITY_TOOLING],
    "redis":              [V.INFRASTRUCTURE],
    "cockroachdb":        [V.INFRASTRUCTURE],
    "snowflake":          [V.ANALYTICS_BI],

    # ─────────────────────────────────────────────────────────────
    # COMMUNICATION & COLLABORATION
    # Messaging, video, email, file sharing, project mgmt
    # Triggers: Internal comms may contain sensitive data
    # ─────────────────────────────────────────────────────────────
    "slack":              [V.COMMUNICATION],
    "microsoft-teams":    [V.COMMUNICATION],
    "zoom":               [V.COMMUNICATION],
    "google-workspace":   [V.COMMUNICATION, V.ANALYTICS_BI],
    "microsoft-365":      [V.COMMUNICATION, V.ANALYTICS_BI],
    "notion":             [V.COMMUNICATION, V.ANALYTICS_BI],
    "confluence":         [V.COMMUNICATION],
    "sharepoint":         [V.COMMUNICATION],
    "dropbox":            [V.COMMUNICATION],
    "box":                [V.COMMUNICATION],
    "loom":               [V.COMMUNICATION],
    "miro":               [V.COMMUNICATION],
    "figma":              [V.COMMUNICATION],
    "webex":              [V.COMMUNICATION],
    "ringcentral":        [V.COMMUNICATION],
    "dialpad":            [V.COMMUNICATION],
    "aircall":            [V.COMMUNICATION],
    "calendly":           [V.COMMUNICATION],
    "asana":              [V.COMMUNICATION],
    "monday":             [V.COMMUNICATION],
    "jira":               [V.COMMUNICATION, V.LEGAL_COMPLIANCE],
    "linear":             [V.COMMUNICATION],
    "basecamp":           [V.COMMUNICATION],
    "clickup":            [V.COMMUNICATION],
    "coda":               [V.COMMUNICATION, V.ANALYTICS_BI],
    "airtable":           [V.COMMUNICATION, V.ANALYTICS_BI],
    "smartsheet":         [V.COMMUNICATION, V.ANALYTICS_BI],

    # ─────────────────────────────────────────────────────────────
    # ANALYTICS & BUSINESS INTELLIGENCE
    # Data warehouse, BI, product analytics, attribution
    # Triggers: Data aggregation risk, AI/ML on your data
    # ─────────────────────────────────────────────────────────────
    "databricks":         [V.ANALYTICS_BI, V.AI_ML],
    "bigquery":           [V.ANALYTICS_BI],
    "redshift":           [V.ANALYTICS_BI],
    "tableau":            [V.ANALYTICS_BI],
    "looker":             [V.ANALYTICS_BI],
    "power-bi":           [V.ANALYTICS_BI],
    "dbt":                [V.ANALYTICS_BI],
    "fivetran":           [V.ANALYTICS_BI],
    "stitch":             [V.ANALYTICS_BI],
    "airbyte":            [V.ANALYTICS_BI],
    "mixpanel":           [V.ANALYTICS_BI],
    "amplitude":          [V.ANALYTICS_BI],
    "heap":               [V.ANALYTICS_BI],
    "fullstory":          [V.ANALYTICS_BI],
    "hotjar":             [V.ANALYTICS_BI],
    "segment":            [V.ANALYTICS_BI, V.CUSTOMER_DATA],
    "rudderstack":        [V.ANALYTICS_BI, V.CUSTOMER_DATA],
    "google-analytics":   [V.ANALYTICS_BI],
    "adobe-analytics":    [V.ANALYTICS_BI],
    "metabase":           [V.ANALYTICS_BI],
    "mode":               [V.ANALYTICS_BI],
    "hex":                [V.ANALYTICS_BI],
    "census":             [V.ANALYTICS_BI, V.CUSTOMER_DATA],
    "hightouch":          [V.ANALYTICS_BI, V.CUSTOMER_DATA],
    "thoughtspot":        [V.ANALYTICS_BI],
    "sisense":            [V.ANALYTICS_BI],
    "qlik":               [V.ANALYTICS_BI],

    # ─────────────────────────────────────────────────────────────
    # IDENTITY & ACCESS MANAGEMENT
    # SSO, MFA, PAM, directory, password management
    # Triggers: Highest access risk - keys to the kingdom
    # ─────────────────────────────────────────────────────────────
    "okta":               [V.IDENTITY_ACCESS],
    "auth0":              [V.IDENTITY_ACCESS],
    "azure-ad":           [V.IDENTITY_ACCESS],
    "google-identity":    [V.IDENTITY_ACCESS],
    "ping-identity":      [V.IDENTITY_ACCESS],
    "onelogin":           [V.IDENTITY_ACCESS],
    "jumpcloud":          [V.IDENTITY_ACCESS],
    "duo":                [V.IDENTITY_ACCESS, V.SECURITY_TOOLING],
    "1password":          [V.IDENTITY_ACCESS, V.SECURITY_TOOLING],
    "lastpass":           [V.IDENTITY_ACCESS],
    "bitwarden":          [V.IDENTITY_ACCESS],
    "hashicorp-vault":    [V.IDENTITY_ACCESS, V.SECURITY_TOOLING],
    "cyberark":           [V.IDENTITY_ACCESS, V.SECURITY_TOOLING],
    "beyondtrust":        [V.IDENTITY_ACCESS, V.SECURITY_TOOLING],
    "sailpoint":          [V.IDENTITY_ACCESS, V.LEGAL_COMPLIANCE],
    "saviynt":            [V.IDENTITY_ACCESS, V.LEGAL_COMPLIANCE],
    "delinea":            [V.IDENTITY_ACCESS, V.SECURITY_TOOLING],
    "keeper":             [V.IDENTITY_ACCESS],

    # ─────────────────────────────────────────────────────────────
    # SECURITY TOOLING
    # SIEM, EDR, vuln management, CSPM, email security
    # Triggers: Access to all systems - highest scrutiny
    # ─────────────────────────────────────────────────────────────
    "crowdstrike":        [V.SECURITY_TOOLING],
    "sentinelone":        [V.SECURITY_TOOLING],
    "carbon-black":       [V.SECURITY_TOOLING],
    "splunk":             [V.SECURITY_TOOLING, V.ANALYTICS_BI],
    "microsoft-sentinel": [V.SECURITY_TOOLING],
    "sumo-logic":         [V.SECURITY_TOOLING, V.ANALYTICS_BI],
    "qualys":             [V.SECURITY_TOOLING],
    "rapid7":             [V.SECURITY_TOOLING],
    "tenable":            [V.SECURITY_TOOLING],
    "wiz":                [V.SECURITY_TOOLING, V.INFRASTRUCTURE],
    "orca":               [V.SECURITY_TOOLING, V.INFRASTRUCTURE],
    "lacework":           [V.SECURITY_TOOLING, V.INFRASTRUCTURE],
    "prisma-cloud":       [V.SECURITY_TOOLING, V.INFRASTRUCTURE],
    "zscaler":            [V.SECURITY_TOOLING, V.INFRASTRUCTURE],
    "netskope":           [V.SECURITY_TOOLING, V.INFRASTRUCTURE],
    "proofpoint":         [V.SECURITY_TOOLING, V.COMMUNICATION],
    "mimecast":           [V.SECURITY_TOOLING, V.COMMUNICATION],
    "knowbe4":            [V.SECURITY_TOOLING],
    "abnormal":           [V.SECURITY_TOOLING],
    "darktrace":          [V.SECURITY_TOOLING, V.AI_ML],
    "vectra":             [V.SECURITY_TOOLING, V.AI_ML],
    "snyk":               [V.SECURITY_TOOLING],
    "veracode":           [V.SECURITY_TOOLING],
    "checkmarx":          [V.SECURITY_TOOLING],
    "drata":              [V.LEGAL_COMPLIANCE],
    "vanta":              [V.LEGAL_COMPLIANCE],

    # ─────────────────────────────────────────────────────────────
    # AI & ML PLATFORMS
    # LLM APIs, AI tools, copilots, automation
    # D6 weight maximum — EU AI Act and FTC apply
    # ─────────────────────────────────────────────────────────────
    "openai":             [V.AI_ML],
    "anthropic":          [V.AI_ML],
    "google-gemini":      [V.AI_ML],
    "cohere":             [V.AI_ML],
    "mistral":            [V.AI_ML],
    "hugging-face":       [V.AI_ML],
    "replicate":          [V.AI_ML],
    "together-ai":        [V.AI_ML],
    "perplexity":         [V.AI_ML],
    "github-copilot":     [V.AI_ML, V.INFRASTRUCTURE],
    "cursor":             [V.AI_ML],
    "codeium":            [V.AI_ML],
    "jasper":             [V.AI_ML, V.CUSTOMER_DATA],
    "copy-ai":            [V.AI_ML],
    "writer":             [V.AI_ML],
    "glean":              [V.AI_ML, V.COMMUNICATION],
    "grammarly":          [V.AI_ML, V.COMMUNICATION],
    "otter":              [V.AI_ML, V.COMMUNICATION],
    "fireflies":          [V.AI_ML, V.COMMUNICATION],
    "harvey":             [V.AI_ML, V.LEGAL_COMPLIANCE],
    "scale-ai":           [V.AI_ML],
    "labelbox":           [V.AI_ML],
    "weights-biases":     [V.AI_ML],
    "langchain":          [V.AI_ML],
    "pinecone":           [V.AI_ML],
    "cohere":             [V.AI_ML],
    "ai21":               [V.AI_ML],
    "stability-ai":       [V.AI_ML],

    # ─────────────────────────────────────────────────────────────
    # PAYMENTS & FINANCIAL TRANSACTIONS
    # Payment gateways, card processing, BNPL, banking APIs
    # PCI DSS considerations for all entries here
    # ─────────────────────────────────────────────────────────────
    "stripe":             [V.PAYMENTS],
    "braintree":          [V.PAYMENTS],
    "paypal":             [V.PAYMENTS],
    "adyen":              [V.PAYMENTS],
    "square":             [V.PAYMENTS],
    "worldpay":           [V.PAYMENTS],
    "checkout":           [V.PAYMENTS],
    "klarna":             [V.PAYMENTS],
    "affirm":             [V.PAYMENTS],
    "afterpay":           [V.PAYMENTS],
    "plaid":              [V.PAYMENTS, V.FINANCIAL_PROCESSING],
    "yodlee":             [V.PAYMENTS, V.FINANCIAL_PROCESSING],
    "marqeta":            [V.PAYMENTS],
    "modern-treasury":    [V.PAYMENTS, V.FINANCIAL_PROCESSING],
    "dwolla":             [V.PAYMENTS],
    "spreedly":           [V.PAYMENTS],
    "chargebee":          [V.PAYMENTS, V.FINANCIAL_PROCESSING],
    "recurly":            [V.PAYMENTS, V.FINANCIAL_PROCESSING],
    "paddle":             [V.PAYMENTS, V.FINANCIAL_PROCESSING],
    "authorize-net":      [V.PAYMENTS],

    # ─────────────────────────────────────────────────────────────
    # HEALTHCARE & CLINICAL
    # EHR, medical devices, telehealth, lab, pharmacy
    # PHI and BAA required for all entries here
    # ─────────────────────────────────────────────────────────────
    "epic":               [V.HEALTHCARE_CLINICAL],
    "cerner":             [V.HEALTHCARE_CLINICAL],
    "meditech":           [V.HEALTHCARE_CLINICAL],
    "athenahealth":       [V.HEALTHCARE_CLINICAL],
    "nextgen":            [V.HEALTHCARE_CLINICAL],
    "allscripts":         [V.HEALTHCARE_CLINICAL],
    "eclinicalworks":     [V.HEALTHCARE_CLINICAL],
    "teladoc":            [V.HEALTHCARE_CLINICAL],
    "mdlive":             [V.HEALTHCARE_CLINICAL],
    "amwell":             [V.HEALTHCARE_CLINICAL],
    "optum":              [V.HEALTHCARE_CLINICAL],
    "change-healthcare":  [V.HEALTHCARE_CLINICAL, V.FINANCIAL_PROCESSING],
    "labcorp":            [V.HEALTHCARE_CLINICAL],
    "quest":              [V.HEALTHCARE_CLINICAL],
    "surescripts":        [V.HEALTHCARE_CLINICAL],
    "health-catalyst":    [V.HEALTHCARE_CLINICAL, V.ANALYTICS_BI],
    "arcadia":            [V.HEALTHCARE_CLINICAL, V.ANALYTICS_BI],
    "veeva":              [V.HEALTHCARE_CLINICAL, V.CUSTOMER_DATA],
    "medidata":           [V.HEALTHCARE_CLINICAL, V.ANALYTICS_BI],
    "flatiron":           [V.HEALTHCARE_CLINICAL, V.ANALYTICS_BI],
    "livongo":            [V.HEALTHCARE_CLINICAL],
    "hinge-health":       [V.HEALTHCARE_CLINICAL],
    "sword-health":       [V.HEALTHCARE_CLINICAL],
    "omada":              [V.HEALTHCARE_CLINICAL],
    "novu-health":        [V.HEALTHCARE_CLINICAL],

    # ─────────────────────────────────────────────────────────────
    # LEGAL & COMPLIANCE / GRC
    # CLM, eDiscovery, compliance automation, GRC platforms
    # Triggers: Access to contracts and legal documents
    # ─────────────────────────────────────────────────────────────
    "ironclad":           [V.LEGAL_COMPLIANCE],
    "docusign":           [V.LEGAL_COMPLIANCE],
    "adobe-sign":         [V.LEGAL_COMPLIANCE],
    "hellosign":          [V.LEGAL_COMPLIANCE],
    "spotdraft":          [V.LEGAL_COMPLIANCE],
    "contractpodai":      [V.LEGAL_COMPLIANCE, V.AI_ML],
    "lexion":             [V.LEGAL_COMPLIANCE, V.AI_ML],
    "relativity":         [V.LEGAL_COMPLIANCE],
    "everlaw":            [V.LEGAL_COMPLIANCE],
    "logikcull":          [V.LEGAL_COMPLIANCE],
    "secureframe":        [V.LEGAL_COMPLIANCE],
    "hyperproof":         [V.LEGAL_COMPLIANCE],
    "onetrust":           [V.LEGAL_COMPLIANCE],
    "trustarc":           [V.LEGAL_COMPLIANCE],
    "osano":              [V.LEGAL_COMPLIANCE],
    "archer":             [V.LEGAL_COMPLIANCE],
    "navex":              [V.LEGAL_COMPLIANCE],
    "riskonnect":         [V.LEGAL_COMPLIANCE],
    "prevalent":          [V.LEGAL_COMPLIANCE],
    "processunity":       [V.LEGAL_COMPLIANCE],
    "onspring":           [V.LEGAL_COMPLIANCE],
    "logicgate":          [V.LEGAL_COMPLIANCE],
    "anecdotes":          [V.LEGAL_COMPLIANCE],
    "tugboat-logic":      [V.LEGAL_COMPLIANCE],
    "strike-graph":       [V.LEGAL_COMPLIANCE],
    "sprinto":            [V.LEGAL_COMPLIANCE],

    # ─────────────────────────────────────────────────────────────
    # SUPPLY CHAIN & LOGISTICS
    # ERP supply modules, logistics, inventory, fleet
    # Triggers: Operational data, employee data if HR module
    # ─────────────────────────────────────────────────────────────
    "manhattan":          [V.SUPPLY_CHAIN],
    "blueyonder":         [V.SUPPLY_CHAIN],
    "kinaxis":            [V.SUPPLY_CHAIN],
    "infor":              [V.SUPPLY_CHAIN, V.FINANCIAL_PROCESSING],
    "epicor":             [V.SUPPLY_CHAIN, V.FINANCIAL_PROCESSING],
    "shipbob":            [V.SUPPLY_CHAIN],
    "flexport":           [V.SUPPLY_CHAIN],
    "freightos":          [V.SUPPLY_CHAIN],
    "project44":          [V.SUPPLY_CHAIN],
    "fourkites":          [V.SUPPLY_CHAIN],
    "samsara":            [V.SUPPLY_CHAIN],
    "fleetcomplete":      [V.SUPPLY_CHAIN],
    "geotab":             [V.SUPPLY_CHAIN],
    "jaggaer":            [V.SUPPLY_CHAIN, V.FINANCIAL_PROCESSING],
    "ivalua":             [V.SUPPLY_CHAIN, V.FINANCIAL_PROCESSING],
    "cin7":               [V.SUPPLY_CHAIN],
    "fishbowl":           [V.SUPPLY_CHAIN],
    "linnworks":          [V.SUPPLY_CHAIN],
    "skubana":            [V.SUPPLY_CHAIN],
    "orderhive":          [V.SUPPLY_CHAIN],
    "tradegecko":         [V.SUPPLY_CHAIN],
    "netsuite-wms":       [V.SUPPLY_CHAIN, V.FINANCIAL_PROCESSING],
    "highjump":           [V.SUPPLY_CHAIN],
    "logiwa":             [V.SUPPLY_CHAIN],
    "shipstation":        [V.SUPPLY_CHAIN],
}


# ─────────────────────────────────────────────────────────────────
# ALIAS MAP
# Common name variations that map to the canonical slug
# ─────────────────────────────────────────────────────────────────
VENDOR_ALIASES: dict[str, str] = {
    # AWS
    "amazon-web-services":   "aws",
    "amazon":                "aws",

    # Google
    "google-cloud":          "gcp",
    "google-cloud-platform": "gcp",
    "g-suite":               "google-workspace",
    "gsuite":                "google-workspace",

    # Microsoft
    "office-365":            "microsoft-365",
    "o365":                  "microsoft-365",
    "m365":                  "microsoft-365",
    "ms-teams":              "microsoft-teams",
    "azure-active-directory":"azure-ad",
    "entra-id":              "azure-ad",

    # Common variations
    "adp-payroll":           "adp",
    "workday-hcm":           "workday",
    "sap-erp":               "sap",
    "oracle-erp":            "oracle",
    "stripe-payments":       "stripe",
    "twilio-sendgrid":       "sendgrid",
    "auth-zero":             "auth0",
    "one-password":          "1password",
    "1pass":                 "1password",
    "crowdstrike-falcon":    "crowdstrike",
    "ms-sentinel":           "microsoft-sentinel",
    "github":                "github-copilot",
    "copilot":               "github-copilot",
    "google-bard":           "google-gemini",
    "bard":                  "google-gemini",
    "chatgpt":               "openai",
    "gpt-4":                 "openai",
    "claude":                "anthropic",
    "gemini":                "google-gemini",
}

# Total count for display
VENDOR_COUNT = len(KNOWN_VENDORS)
CATEGORY_COUNTS = {
    "Financial Processing":    26,
    "HR & People":             29,
    "Customer Data":           27,
    "Infrastructure":          28,
    "Communication":           27,
    "Analytics & BI":          27,
    "Identity & Access":       18,
    "Security Tooling":        25,
    "AI & ML":                 27,
    "Payments":                20,
    "Healthcare & Clinical":   25,
    "Legal & Compliance":      25,
    "Supply Chain":            25,
}
