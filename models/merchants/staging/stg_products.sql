{{ config(materialized='view') }}

SELECT
    product_id
    , product_name
    , list_price_in_cents / 100.0 AS list_price
FROM {{ ref('base_products') }}
