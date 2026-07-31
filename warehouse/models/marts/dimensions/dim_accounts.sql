with accounts as (
    select *
    from {{ref("stg_core__accounts")}}
)

select
    md5(
        cast(source_system_id as text)
        || '|'
        || external_account_id
    ) as account_key,
    account_id,
    source_system_id,
    external_account_id,
    currency_code,
    coalesce(account_type, 'unknown') as account_type,
    coalesce(status, 'unknown') as account_status,
    opened_at,
    created_at,
    updated_at
from accounts