{{ config(materialized='view') }}

select
    merchant_id
    , merchant_name
    , customer_type
    , tier
    , cast(merchant_created_at as timestamp) as merchant_created_at
from {{ ref('base_merchants') }}
