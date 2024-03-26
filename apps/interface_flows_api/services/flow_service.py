from PIL import Image

from apps.interface_flows_api.repositories.flow_repository import \
    FlowRepository
from apps.interface_flows_api.services.auth_service import AuthService
from apps.interface_flows_api.services.ml_provider import \
    MachineLearningProvider


class FlowService:
    repository = FlowRepository()
    ml_provider = MachineLearningProvider()

    @staticmethod
    def _get_frame_size(image_file):
        image = Image.open(image_file)
        width, height = image.size
        return width, height

    def _compute_flow_frames_positions(self, flow) -> None:
        frames = self.repository.get_all_flow_frames(flow)
        graph = {}

        for frame in frames:
            graph[frame] = self.repository.get_all_frame_connected_frames(frame)

        height = []
        stack = [(max(graph, key=lambda x: len(graph[x])), 0)]
        visited = set()

        while len(stack) > 0:
            current_frame, pos_x = stack.pop()

            if len(height) <= pos_x:
                height.append(0)

            pos_y = height[pos_x]
            height[pos_x] += 1

            self.repository.update_frame_pos(current_frame, pos_x, pos_y)

            visited.add(current_frame)
            connected_frames = graph[current_frame]

            for frame in connected_frames:
                if frame not in visited:
                    stack.append((frame, pos_x + 1))

            if len(stack) == 0:
                not_visited = list(visited - set(graph.keys()))
                if len(not_visited) == 0:
                    break
                stack.append((graph[not_visited[0]], 0))

    def get_flow_by_id(self, flow_id: int, user=None):
        profile = AuthService().get_profile(user)
        return self.repository.get_flow_by_id(flow_id=flow_id, profile=profile)

    def get_public_flows(
        self, sort: str = "date", order: str = "ASC", limit: int = 10, offset: int = 0
    ):
        return self.repository.get_public_flows(sort, order, limit, offset)

    def get_available_flows(self):
        return self.repository.get_available_flows()

    def create_new_flow(
        self, title: str = "Flow Title", description: str = "Flow Desc", frames=None
    ):
        width, height = self._get_frame_size(frames[0])
        flow = self.repository.add_flow(title, description, height, width)

        predictions = self.ml_provider.get_direct_graph(frames)
        previous_frame = None

        for i, prediction in enumerate(predictions):
            frame = self.repository.add_frame(
                flow=flow, image=frames[prediction["index"]]
            )
            if (
                i > 0
                and predictions[i]["time_out"] - predictions[i - 1]["time_in"] < 100
            ):
                self.repository.add_connection(frame_out=previous_frame, frame_in=frame)

            previous_frame = frame

        self._compute_flow_frames_positions(flow)

        return flow
