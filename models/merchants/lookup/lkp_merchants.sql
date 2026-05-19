{{ config(materialized='table') }}

SELECT
    merchant_id
    , merchant_name
    , customer_type
    , tier
    , merchant_created_at
FROM {{ ref('stg_merchants') }}
