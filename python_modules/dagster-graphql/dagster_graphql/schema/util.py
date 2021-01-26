import graphene


def non_null_list(of_type):
    return graphene.NonNull(graphene.List(graphene.NonNull(of_type)))
