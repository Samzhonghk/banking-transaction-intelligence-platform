with transactions as(
    select *
    from {{ ref("stg_core__transactions")}}
),

accounts as (
    select *
    from {{ ref("dim_accounts")}}
)

select
    md5(
        accounts.account_key
        || '|'
        || transactions.external_transaction_id
    ) as transaction_key,
    transactions.transaction_id,
    transactions.raw_transaction_id,
    accounts.account_key,
    transactions.external_transaction_id,
    transactions.amount,
    transactions.currency_code,
    transactions.description,
    transactions.transaction_timestamp,
    cast(
        transactions.transaction_timestamp at time zone 'utc'
        AS date
    ) as transaction_date,
    transactions.created_at
from transactions
inner join accounts
    on transactions.account_id = accounts.account_id