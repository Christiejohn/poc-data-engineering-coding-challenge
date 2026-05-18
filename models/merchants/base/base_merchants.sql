{{ config(materialized='view') }}
select * from {{ source('raw', 'merchants') }}
