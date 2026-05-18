{{ config(materialized='view') }}

SELECT
    merchant_id
    , merchant_name
    , customer_type
    , tier
    , CAST(merchant_created_at AS timestamp) AS merchant_created_at
FROM {{ ref('base_merchants') }}
