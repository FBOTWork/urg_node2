# Copyright 2022 eSOL Co.,Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import launch
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch.actions import (DeclareLaunchArgument, EmitEvent, RegisterEventHandler)
from launch.event_handlers import OnProcessStart
from launch.events import matches_action
from launch_ros.actions import LifecycleNode
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events.lifecycle import ChangeState
from lifecycle_msgs.msg import Transition

    # 2台のLiDARを接続する場合のurg_node2の多重起動

def generate_launch_description():

    # パラメータファイルのパス設定（1台目）
    config_file_path_front = os.path.join(
        get_package_share_directory('urg_node2'),
        'config',
        'params_serial_front.yaml'
    )

    # パラメータファイルのパス設定（2台目）
    config_file_path_rear = os.path.join(
        get_package_share_directory('urg_node2'),
        'config',
        'params_serial_rear.yaml'
    )

    # パラメータファイルの読み込み（1台目）
    with open(config_file_path_front, 'r') as file:
        config_params_front = yaml.safe_load(file)['urg_node2']['ros__parameters']

    # パラメータファイルの読み込み（2台目）
    with open(config_file_path_rear, 'r') as file:
        config_params_rear = yaml.safe_load(file)['urg_node2']['ros__parameters']

    # ライフサイクルノードとしてのurg_node2の初期化（1台目）
    lifecycle_node_front = LifecycleNode(
        package='urg_node2',
        executable='urg_node2_node',
        name=LaunchConfiguration('node_name_front'),
        remappings=[('scan', LaunchConfiguration('scan_topic_name_front'))],
        parameters=[config_params_front],
        namespace='',
        output='screen',
    )

    # ライフサイクルノードとしてのurg_node2の初期化（2台目）
    lifecycle_node_rear = LifecycleNode(
        package='urg_node2',
        executable='urg_node2_node',
        name=LaunchConfiguration('node_name_rear'),
        remappings=[('scan', LaunchConfiguration('scan_topic_name_rear'))],
        parameters=[config_params_rear],
        namespace='',
        output='screen',
    )

    # Unconfigure から Inactive への状態遷移（auto_start が true の場合に実行）（1台目）
    urg_node2_node_front_configure_event_handler = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=lifecycle_node_front,
            on_start=[
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=matches_action(lifecycle_node_front),
                        transition_id=Transition.TRANSITION_CONFIGURE,
                    ),
                ),
            ],
        ),
        condition=IfCondition(LaunchConfiguration('auto_start')),
    )

    # Inactive から Active への状態遷移（auto_start が true の場合に実行）（1台目）
    urg_node2_node_front_activate_event_handler = RegisterEventHandler(
        event_handler=OnStateTransition(
            target_lifecycle_node=lifecycle_node_front,
            start_state='configuring',
            goal_state='inactive',
            entities=[
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=matches_action(lifecycle_node_front),
                        transition_id=Transition.TRANSITION_ACTIVATE,
                    ),
                ),
            ],
        ),
        condition=IfCondition(LaunchConfiguration('auto_start')),
    )

    # Unconfigure から Inactive への状態遷移（auto_start が true の場合に実行）（2台目）
    urg_node2_node_rear_configure_event_handler = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=lifecycle_node_rear,
            on_start=[
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=matches_action(lifecycle_node_rear),
                        transition_id=Transition.TRANSITION_CONFIGURE,
                    ),
                ),
            ],
        ),
        condition=IfCondition(LaunchConfiguration('auto_start')),
    )

    # Inactive から Active への状態遷移（auto_start が true の場合に実行）（2台目）
    urg_node2_node_rear_activate_event_handler = RegisterEventHandler(
        event_handler=OnStateTransition(
            target_lifecycle_node=lifecycle_node_rear,
            start_state='configuring',
            goal_state='inactive',
            entities=[
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=matches_action(lifecycle_node_rear),
                        transition_id=Transition.TRANSITION_ACTIVATE,
                    ),
                ),
            ],
        ),
        condition=IfCondition(LaunchConfiguration('auto_start')),
    )

    # 引数について
    # auto_start          : 起動時に自動で Active 状態へ遷移させる（デフォルト）true
    # node_name_front     : 1台目のノード名（デフォルト）"urg_node2_front"
    # node_name_rear      : 2台目のノード名（デフォルト）"urg_node2_rear"
    # scan_topic_name_front : トピック名（デフォルト）"scan_front" ※マルチエコー非対応
    # scan_topic_name_rear : トピック名（デフォルト）"scan_rear" ※マルチエコー非対応
    # ※マルチエコーを利用する場合は、上記のノード初期化セクションの remappings を直接編集してください
    # ※読み込むパラメータファイルを変更するには、上記ファイルのファイル名を直接編集してください
    return LaunchDescription([
        DeclareLaunchArgument('auto_start', default_value='true'),
        DeclareLaunchArgument('node_name_front', default_value='urg_node2_front'),
        DeclareLaunchArgument('node_name_rear', default_value='urg_node2_rear'),
        DeclareLaunchArgument('scan_topic_name_front', default_value='scan_front'),
        DeclareLaunchArgument('scan_topic_name_rear', default_value='scan_rear'),
        lifecycle_node_front,
        lifecycle_node_rear,
        urg_node2_node_front_configure_event_handler,
        urg_node2_node_front_activate_event_handler,
        urg_node2_node_rear_configure_event_handler,
        urg_node2_node_rear_activate_event_handler,
    ])