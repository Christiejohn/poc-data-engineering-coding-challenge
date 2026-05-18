{{ config(
    materialized='incremental',
    unique_key='order_id'
) }}

with shipment_lines as (
    select
        sl.shipment_id
        , sl.line_item_id
        , sl.quantity_shipped
        , li.unit_price
    from {{ ref('stg_shipment_line_items') }} as sl
    inner join {{ ref('stg_line_items') }} as li
        on sl.line_item_id = li.line_item_id
)

, joined as (
    select
        o.order_id
        , o.merchant_id
        , o.customer_id
        , o.order_status
        , o.is_test
        , o.ordered_at
        , o.paid_at
        , s.shipment_id
        , s.shipped_at
        , sl.line_item_id
        , sl.quantity_shipped
        , sl.unit_price
    from {{ ref('stg_orders') }} as o
    left join {{ ref('stg_shipments') }} as s
        on o.order_id = s.order_id
    left join shipment_lines as sl
        on s.shipment_id = sl.shipment_id
)

, shipment_totals as (
    -- aggregated to one row per (order, shipment)
    select
        order_id
        , merchant_id
        , customer_id
        , order_status
        , is_test
        , ordered_at
        , paid_at
        , shipment_id
        , shipped_at
        , count(distinct line_item_id) as line_count
        , sum(quantity_shipped) as total_quantity
        , sum(quantity_shipped * unit_price) as shipment_revenue
    from joined
    group by 1, 2, 3, 4, 5, 6, 7, 8, 9
)

, shipment_counts as (
    select
        order_id
        , count(distinct shipment_id) as shipment_count
    from shipment_totals
    group by 1
)

, enriched as (
    select
        st.order_id
        , st.merchant_id
        , m.merchant_name
        , st.customer_id
        , m.customer_type
        , st.order_status
        , st.is_test
        , st.ordered_at
        , st.paid_at
        , st.shipped_at
        , sc.shipment_count
        , st.line_count
        , st.total_quantity
        , st.shipment_revenue as revenue
    from shipment_totals as st
    left join {{ ref('lkp_merchants') }} as m
        on st.merchant_id = m.merchant_id
    left join shipment_counts as sc
        on st.order_id = sc.order_id
)

select
    order_id
    , merchant_id
    , merchant_name
    , customer_id
    , customer_type
    , order_status
    , is_test
    , ordered_at
    , paid_at
    , shipped_at
    , shipment_count
    , line_count
    , total_quantity
    , revenue
    , current_timestamp as created_at_dwh
    , current_timestamp as updated_at_dwh
from enriched
-- dedupe to one row per order (orders can have multiple shipments)
qualify row_number() over (partition by order_id order by shipped_at) = 1

{% if is_incremental() %}
where ordered_at >= {{ get_incremental_value('updated_at_dwh') }}
{% endif %}
