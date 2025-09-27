select
    cast("Review Id" as varchar)       as review_id,
    trim("Reviewer Name")              as reviewer_name,
    trim("Review Title")               as review_title,
    cast("Review Rating" as integer)   as review_rating,
    "Review Content"                   as review_content,
    "Review IP Address"                as review_ip_address,
    cast("Business Id" as varchar)     as business_id,
    trim("Business Name")              as business_name,
    cast("Reviewer Id" as varchar)     as reviewer_id,
    trim("Email Address")              as email_address,
    trim("Reviewer Country")           as reviewer_country,
    try_cast("Review Date" as date)    as review_date
from {{ ref('tp_reviews') }}