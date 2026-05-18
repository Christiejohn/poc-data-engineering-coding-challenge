{{ config(materialized='view') }}

select
    shipment_line_item_id
    , shipment_id
    , line_item_id
    , quantity_shipped
from {{ ref('base_shipment_line_items') }}
