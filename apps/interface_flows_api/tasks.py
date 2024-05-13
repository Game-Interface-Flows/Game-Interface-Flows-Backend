import logging

from celery import shared_task

from apps.interface_flows_api.models import Flow, FlowProcessStatus
from apps.interface_flows_api.services.flow_build_service import \
    flow_build_service

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@shared_task
def flow_builder(flow_id: int, video_file_path: str, interval: int):
    flow = Flow.objects.get(pk=flow_id)
    try:
        flow_build_service.build_flow(
            flow=flow, video_file_path=video_file_path, interval=interval
        )
        flow.process = FlowProcessStatus.SUCCESS
    except Exception as e:
        logger.error(f"Error processing flow {flow_id}: {e}", exc_info=True)
        flow.process = FlowProcessStatus.FAIL
    flow.save()
