{{ config(materialized='table') }}

select
    product_id
    , product_name
    , list_price
from {{ ref('stg_products') }}
