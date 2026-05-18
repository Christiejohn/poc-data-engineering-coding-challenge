{{ config(materialized='view') }}

select
    product_id
    , product_name
    , list_price_in_cents / 100.0 as list_price
from {{ ref('base_products') }}
