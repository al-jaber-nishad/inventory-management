from .bank import urlpatterns as bank_patterns
from .group import urlpatterns as group_patterns
from .primarygroup import urlpatterns as primarygroup_patterns
from .ledgeraccount import urlpatterns as ledgeraccount_patterns
from .subledgeraccount import urlpatterns as subledgeraccount_patterns

urlpatterns = [
    *bank_patterns,
    *group_patterns,
    *primarygroup_patterns,
    *ledgeraccount_patterns,
    *subledgeraccount_patterns,
]