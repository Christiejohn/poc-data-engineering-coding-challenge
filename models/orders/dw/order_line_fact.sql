{{ config(
    materialized='incremental',
    unique_key='line_item_id'
) }}

select
    li.line_item_id
    , li.order_id
    , li.product_id
    , li.quantity
    , li.unit_price
    , li.quantity * li.unit_price as line_revenue
    , current_timestamp as created_at_dwh
    , current_timestamp as updated_at_dwh
from {{ ref('stg_line_items') }} as li

{% if is_incremental() %}
where li.line_item_id not in (select line_item_id from {{ this }})
{% endif %}
