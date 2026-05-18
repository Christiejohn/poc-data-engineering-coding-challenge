{{ config(materialized='view') }}

select
    line_item_id
    , order_id
    , product_id
    , quantity
    , unit_price_in_cents / 100.0 as unit_price
    , line_status
from {{ ref('base_line_items') }}
