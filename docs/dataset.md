# Dataset

## Selection
| Option | Focus | Timestamps | Labels | Decision |
|---|---|---|---|---|
| IBM AML (HI-Small) | Money laundering | Yes | Is Laundering | **Selected** |
| PaySim | Mobile-money fraud | Hourly steps only | isFraud | Not selected |

**Rationale:** The IBM dataset was designed for AML research and includes timestamps and payment formats, which the structuring and rapid-movement rules need.

## Source
- Name: IBM Transactions for Anti Money Laundering (HI-Small)
- Source: [Kaggle](https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml)
- File: HI-Small_Trans.csv
- License: Community Data License Agreement – Sharing – Version 1.0
- Size: 5,078,345 rows, 475.66 MB

## Data dictionary
| Field | Type | Description |
|---|---|---|
| Timestamp | datetime | Date and time of transaction |
| From Bank | integer | Sending bank ID |
| Account | string | Sending account ID |
| To Bank | integer | Receiving bank ID |
| Account (2nd) | string | Receiving account ID (loaded as "Account.1" in pandas) |
| Amount Received | decimal | Amount credited |
| Receiving Currency | string | Currency received |
| Amount Paid | decimal | Amount debited |
| Payment Currency | string | Currency paid |
| Payment Format | string | Cash, wire, ACH, cheque, etc. |
| Is Laundering | integer | 1 = laundering, 0 = legitimate |

## How to get the data
Download HI-Small_Trans.csv from the source above and place it in a local `data/` folder.

## Assumptions
- Synthetic data; typologies may not match real-world patterns.
