with source as(
    select *
    from {{ source("core", "accounts")}}
)

select
    id as account_id,
    source_system_id,
    external_account_id,
    currency_code,
    account_type,
    status,
    opened_at,
    created_at,
    updated_at
from source