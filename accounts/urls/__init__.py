from .bank import urlpatterns as bank_patterns
from .group import urlpatterns as group_patterns
from .primarygroup import urlpatterns as primarygroup_patterns
from .ledgeraccount import urlpatterns as ledgeraccount_patterns
from .subledgeraccount import urlpatterns as subledgeraccount_patterns
from .paymentvoucher import urlpatterns as paymentvoucher_patterns
from .receiptvoucher import urlpatterns as receiptvoucher_patterns
from .balance_sheet import urlpatterns as balance_sheet_patterns

urlpatterns = [
    *bank_patterns,
    *group_patterns,
    *primarygroup_patterns,
    *ledgeraccount_patterns,
    *subledgeraccount_patterns,
    *paymentvoucher_patterns,
    *receiptvoucher_patterns,
    *balance_sheet_patterns,
]