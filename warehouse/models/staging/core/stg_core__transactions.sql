with source as(
    select *
    from {{source("core", "transactions")}}
)

select
    id as transaction_id,
    raw_transaction_id,
    account_id,
    external_transaction_id,
    amount,
    currency_code,
    description,
    transaction_timestamp,
    created_at
from source