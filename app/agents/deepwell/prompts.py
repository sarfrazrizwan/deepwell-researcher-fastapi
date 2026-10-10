APPROVE_BRIEF_CLASSIFICATION_SYS_PROMPT=""""
The user was shown a research brief. Decide if they approve it or want changes. 'yes', 'continue', 'looks good' mean approved. 
Any requested change means revise; extract it into feedback.

If to revise, write feedback for user with acknowledgement.
"""


APPROVE_BRIEF_CLASSIFICATION_PROMPT="""
Her is the original research brief 
<brief>
{brief}
</brief>

<user_reply>
{user_reply}
</user_reply>
"""
