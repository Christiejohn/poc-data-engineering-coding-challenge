{{ config(materialized='view') }}

SELECT
    shipment_line_item_id
    , shipment_id
    , line_item_id
    , quantity_shipped
FROM {{ ref('base_shipment_line_items') }}
