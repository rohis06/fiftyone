"""
FiftyOne Server /frames route

| Copyright 2017-2024, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
from starlette.endpoints import HTTPEndpoint
from starlette.responses import JSONResponse
from starlette.requests import Request

from fiftyone.core.expressions import ViewField as F
import fiftyone.core.json as foj
import fiftyone.core.odm as foo
import fiftyone.core.view as fov

from fiftyone.server.decorators import route
import fiftyone.core.media as fom
import fiftyone.server.view as fosv


class Frames(HTTPEndpoint):
    @route
    async def post(self, request: Request, data: dict):
        start_frame = int(data.get("frameNumber", 1))
        frame_count = int(data.get("frameCount", 1))
        num_frames = int(data.get("numFrames"))
        extended = data.get("extended", None)
        dataset = data.get("dataset")
        stages = data.get("view")
        sample_id = data.get("sampleId")
        group_slice = data.get("slice", None)

        view = fosv.get_view(dataset, stages=stages, extended_stages=extended)
        view = fov.make_optimized_select_view(view, sample_id)

        if view.media_type == fom.GROUP and group_slice is not None:
            view.group_slice = group_slice

        end_frame = min(num_frames + start_frame, frame_count)
        support = None if stages else [start_frame, end_frame]
        if not support:
            view = view.set_field(
                "frames",
                F("frames").filter(
                    (F("frame_number") >= start_frame)
                    & (F("frame_number") <= end_frame)
                ),
            )

        frames = await foo.aggregate(
            foo.get_async_db_conn()[view._dataset._sample_collection_name],
            view._pipeline(frames_only=True, support=support),
        ).to_list(end_frame - start_frame + 1)

        return JSONResponse(
            {
                "frames": foj.stringify(frames),
                "range": [start_frame, end_frame],
            }
        )
