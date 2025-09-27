with ranked_reviews as (
    select
        *,
        row_number() over (
            partition by review_id
            order by review_date desc nulls last, reviewer_id, business_id
        ) as review_rank
    from {{ ref('stg_tp_reviews') }}
    where review_id is not null
)

select
    review_id,
    reviewer_id,
    business_id,

    nullif(trim(reviewer_name), '') as reviewer_name,
    nullif(trim(business_name), '') as business_name,
    nullif(trim(review_title), '')  as review_title,
    nullif(trim(review_content), '') as review_content,

    case
        when review_rating between 1 and 5 then review_rating
        else null
    end as review_rating,

    trim(review_ip_address)        as review_ip_address,
    lower(trim(email_address))     as email_address,
    upper(nullif(trim(reviewer_country), '')) as reviewer_country,

    review_date
from ranked_reviews
where review_rank = 1
