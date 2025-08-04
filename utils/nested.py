




def getNestedCatsByParent(parent):
    def dfs(node, vals):
        children = node.children.all()
        if children.count() < 1:
            return
        vals.extend([child for child in children])
        for child in children:
            dfs(child, vals)    
    vals = list()
    dfs(parent, vals)
    return vals