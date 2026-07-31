with transactions as(
    select *
    from {{ref("fct_transactions")}}
)

select 
    md5(
        cast(transaction_date as text)
        || '|'
        || currency_code

    ) as daily_summary_key,
    transaction_date,
    currency_code,
    count(*) as transaction_count,
    count(distinct account_key) as active_account_count,
    sum(amount) as total_amount,
    avg(amount) as average_amount,
    min(amount) as minimum_amount,
    max(amount) as maximum_amount
from transactions
group by
    transaction_date,
    currency_code