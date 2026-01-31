# Example Client Configuration

Create `clients.xlsx` with the following structure:

## Required Columns

| Column Name | Description | Example |
|-------------|-------------|---------|
| `client_name` | Display name for the client | Acme Corporation |
| `gsc_property` | Google Search Console property URL | https://www.acme.com/ |
| `ga4_property_id` | Google Analytics 4 property ID | 123456789 |
| `client_tag` | Short identifier (optional) | acme |

## Example Data

| client_name | gsc_property | ga4_property_id | client_tag |
|-------------|--------------|-----------------|------------|
| Acme Corporation | https://www.acme.com/ | 123456789 | acme |
| Beta Industries | https://www.betaindustries.com/ | 987654321 | beta |
| Gamma Services | https://www.gammaservices.io/ | 456789123 | gamma |

## Notes

- `gsc_property` must match exactly as shown in Google Search Console
- `ga4_property_id` is the numeric property ID (not the measurement ID)
- Leave cells empty if a service is not configured for that client
