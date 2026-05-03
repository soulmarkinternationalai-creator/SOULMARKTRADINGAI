export default function NotificationsPanel({ notifications }) {
  return (
    <div className="notifications">
      <h3>Notifications</h3>
      {notifications.length === 0 ? (
        <p className="empty">No notifications</p>
      ) : (
        <div className="notification-list">
          {notifications.slice(0, 15).map(n => (
            <div key={n.id} className="notification-item">
              <span className="time">{new Date(n.timestamp).toLocaleTimeString()}</span>
              <span className="message">{n.message}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
