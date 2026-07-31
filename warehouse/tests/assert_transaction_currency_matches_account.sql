select
    transactions.transaction_key,
    transactions.currency_code as transaction_currency,
    accounts.currency_code as account_currency
from {{ref("fct_transactions")}} as transactions
inner join {{ref("dim_accounts")}} as accounts
    on transactions.account_key = accounts.account_key
where transactions.currency_code<>accounts.currency_code