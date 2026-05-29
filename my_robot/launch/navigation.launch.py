from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os

def generate_launch_description():
    pkg_share = FindPackageShare('my_robot').find('my_robot')
    map_file = os.path.join(pkg_share, 'config', 'maps', 'my_map.yaml')
    params_file = os.path.join(pkg_share, 'config', 'nav2_params.yaml')

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([pkg_share, 'launch', 'gazebo.launch.py'])
        ])
    )

    bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([FindPackageShare('nav2_bringup'), 'launch', 'bringup_launch.py'])
        ]),
        launch_arguments={
            'params_file': params_file,
            'map': map_file,
            'slam': 'False',
            'use_localization': 'True',
            'autostart': 'true',
            'use_composition': 'True',
            'use_sim_time': 'True',
        }.items()
    )

    rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([FindPackageShare('nav2_bringup'), 'launch', 'rviz_launch.py'])
        ]),
        launch_arguments={
            'use_sim_time': 'True',
            'rviz_config': os.path.join(pkg_share, 'config', 'view.rviz')
        }.items()
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        clock_bridge,
        gazebo_launch,
        TimerAction(period=12.0, actions=[bringup_launch, rviz_launch])
    ])