#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, PointStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rclpy.duration import Duration

class WaypointCollector(Node):
    def __init__(self):
        super().__init__('waypoint_collector')
        
        # Subscriber for clicked points from RViz (Publish Point tool)
        self.subscription = self.create_subscription(
            PointStamped,
            '/clicked_point',
            self.point_callback,
            10)
        
        self.waypoints = []
        self.navigator = BasicNavigator()
        
        self.get_logger().info('Waypoint Collector Node Started')
        self.get_logger().info('Use the "Publish Point" tool in RViz to add waypoints.')
        self.get_logger().info('Once you have added all points, the robot will start following them.')
        self.get_logger().info('Press Ctrl+C to stop collecting and start navigation (or implement a trigger).')

    def point_callback(self, msg):
        wp = PoseStamped()
        wp.header.frame_id = msg.header.frame_id
        wp.header.stamp = msg.header.stamp
        wp.pose.position.x = msg.point.x
        wp.pose.position.y = msg.point.y
        wp.pose.position.z = msg.point.z
        wp.pose.orientation.w = 1.0 # Default orientation
        
        self.waypoints.append(wp)
        self.get_logger().info(f'Added waypoint {len(self.waypoints)}: x={wp.pose.position.x:.2f}, y={wp.pose.position.y:.2f}')

    def start_waypoint_following(self):
        if not self.waypoints:
            self.get_logger().warn('No waypoints collected!')
            return

        self.get_logger().info(f'Starting waypoint following for {len(self.waypoints)} points...')
        
        # Wait for Nav2 to be active
        self.navigator.waitUntilNav2Active()

        # Start following waypoints
        self.navigator.followWaypoints(self.waypoints)

        i = 0
        while not self.navigator.isTaskComplete():
            i = i + 1
            feedback = self.navigator.getFeedback()
            if feedback and i % 5 == 0:
                self.get_logger().info('Executing current waypoint: ' +
                                       str(feedback.current_waypoint + 1) + '/' + str(len(self.waypoints)))

        result = self.navigator.getResult()
        if result == TaskResult.SUCCEEDED:
            self.get_logger().info('Goal succeeded!')
        elif result == TaskResult.CANCELED:
            self.get_logger().info('Goal was canceled!')
        elif result == TaskResult.FAILED:
            self.get_logger().info('Goal failed!')
        else:
            self.get_logger().info('Goal has an invalid return status!')

def main(args=None):
    import threading
    
    rclpy.init(args=args)
    collector = WaypointCollector()
    
    # Run spinning in a background thread
    spin_thread = threading.Thread(target=rclpy.spin, args=(collector,), daemon=True)
    spin_thread.start()
    
    try:
        input("\nPress ENTER to start following waypoints, or Ctrl+C to exit...\n")
        collector.start_waypoint_following()
        
        # Wait for navigation to finish (keep spinning)
        while rclpy.ok():
            import time
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        collector.get_logger().info('Exiting...')
    finally:
        collector.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
