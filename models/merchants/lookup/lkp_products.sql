{{ config(materialized='table') }}

SELECT
    product_id
    , product_name
    , list_price
FROM {{ ref('stg_products') }}
