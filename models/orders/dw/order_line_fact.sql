{{ config(
    materialized='incremental',
    unique_key='line_item_id'
) }}

SELECT
    li.line_item_id
    , li.order_id
    , li.product_id
    , li.quantity
    , li.unit_price
    , li.quantity * li.unit_price AS line_revenue
    , current_timestamp AS created_at_dwh
    , current_timestamp AS updated_at_dwh
FROM {{ ref('stg_line_items') }} AS li

{% if is_incremental() %}
    WHERE li.line_item_id NOT IN (SELECT t.line_item_id FROM {{ this }} AS t)
{% endif %}
