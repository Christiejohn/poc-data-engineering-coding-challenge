{{ config(materialized='view') }}

SELECT
    line_item_id
    , order_id
    , product_id
    , quantity
    , unit_price_in_cents / 100.0 AS unit_price
    , line_status
FROM {{ ref('base_line_items') }}
