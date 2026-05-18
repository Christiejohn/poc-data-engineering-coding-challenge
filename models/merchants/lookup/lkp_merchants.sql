{{ config(materialized='table') }}

select
    merchant_id
    , merchant_name
    , customer_type
    , tier
    , merchant_created_at
from {{ ref('stg_merchants') }}
