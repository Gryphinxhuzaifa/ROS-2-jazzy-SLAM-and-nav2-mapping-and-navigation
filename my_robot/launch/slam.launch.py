from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import os

def generate_launch_description():
    pkg_share = FindPackageShare('my_robot').find('my_robot')
    config_dir = os.path.join(pkg_share, 'config')
    slam_config = os.path.join(config_dir, 'slam_online.yaml')
    nav2_config = os.path.join(config_dir, 'nav2_slam.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    # 🔧 1️⃣ Clock Bridge (MANDATORY for Gazebo Harmonic + Jazzy)
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen'
    )

    # 2️ Gazebo + Robot Spawn
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([pkg_share, 'launch', 'gazebo.launch.py'])
        ])
    )

    # 3️ SLAM Toolbox (Online Async)
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([FindPackageShare('slam_toolbox'), 'launch', 'online_async_launch.py'])
        ]),
        launch_arguments={
            'slam_params_file': slam_config,
            'use_sim_time': use_sim_time
        }.items()
    )

    # 4️⃣ Nav2 (SLAM Mode)
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([FindPackageShare('nav2_bringup'), 'launch', 'bringup_launch.py'])
        ]),
        launch_arguments={
            'params_file': nav2_config,
            'use_sim_time': use_sim_time,
            'map': ''  # Empty = SLAM mode
        }.items()
    )

    # 5️⃣ RViz2
    rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([FindPackageShare('nav2_bringup'), 'launch', 'rviz_launch.py'])
        ]),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        clock_bridge,
        gazebo_launch,
        TimerAction(period=3.0, actions=[slam_launch]),
        TimerAction(period=5.0, actions=[nav2_launch, rviz_launch])
    ])