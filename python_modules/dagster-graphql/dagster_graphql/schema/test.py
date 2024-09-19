import asyncio

import graphene

_STATE = {}


class GrapheneTestFields(graphene.ObjectType):
    class Meta:
        name = "TestFields"

    alwaysException = graphene.String()
    asyncString = graphene.String()

    def resolve_alwaysException(self, _):
        raise Exception("as advertised")

    async def resolve_asyncString(self, _):
        msg = "slept"
        if _STATE.get("sleeping"):
            msg += " concurrently"
        else:
            _STATE["sleeping"] = True

        await asyncio.sleep(0)
        _STATE["sleeping"] = False
        return msg
