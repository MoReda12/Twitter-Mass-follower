# Twitter Follow Bot

A sophisticated Twitter automation tool designed to manage Twitter following operations, featuring advanced account management, proxy support, and comprehensive analytics.

## Features

- **Multi-Account Management**: Handle multiple Twitter accounts simultaneously
- **Proxy Support**: Configure and use proxies for enhanced security and IP rotation
- **Advanced Analytics**: Track and analyze following activities
- **User-Friendly GUI**: Modern interface with multiple tabs for different functionalities
- **Account Management**:
  - Add/remove accounts
  - View account details
  - Track account status
- **Proxy Management**:
  - Add/remove proxies
  - Test proxy connections
  - Configure proxy settings
- **Analytics Dashboard**:
  - View following statistics
  - Track account growth
  - Monitor activity logs
- **Customizable Settings**:
  - Adjust following limits
  - Configure delay settings
  - Set proxy preferences

## Requirements

- Python 3.x
- Chrome browser installed
- Required Python packages:
  ```
  tkinter
  selenium
  webdriver_manager
  ttkthemes
  ```

## Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd twitter-follow-bot
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Make sure you have Chrome browser installed on your system

## Usage

1. Run the application:
   ```bash
   python follow.py
   ```

2. In the application:
   - **Accounts Tab**:
     - Add Twitter accounts with credentials
     - View account status and details
     - Manage account settings
   
   - **Proxies Tab**:
     - Add proxy configurations
     - Test proxy connections
     - Manage proxy settings
   
   - **Analytics Tab**:
     - View following statistics
     - Monitor account growth
     - Check activity logs
   
   - **Settings Tab**:
     - Configure following limits
     - Adjust delay settings
     - Set proxy preferences

## Configuration

### Account Settings
- Username and password format: `username:password`
- Account status tracking
- Activity monitoring

### Proxy Settings
- Proxy format: `ip:port:username:password`
- Connection testing
- Proxy rotation options

### Analytics Settings
- Following limits
- Activity tracking
- Growth monitoring

## Security Features

- **Proxy Support**: Protect your IP address
- **Rate Limiting**: Built-in delays to prevent account restrictions
- **Account Protection**: Secure credential storage
- **Activity Monitoring**: Track and log all actions

## Best Practices

1. **Account Safety**:
   - Use different proxies for each account
   - Maintain reasonable following limits
   - Monitor account activity regularly

2. **Proxy Usage**:
   - Test proxies before use
   - Rotate proxies regularly
   - Use high-quality proxy services

3. **Following Strategy**:
   - Follow relevant accounts
   - Maintain engagement ratios
   - Avoid aggressive following

## Troubleshooting

### Common Issues

1. **Proxy Connection Failed**
   - Check proxy credentials
   - Verify proxy server status
   - Test proxy connection

2. **Account Login Issues**
   - Verify credentials
   - Check account status
   - Try different proxy

3. **Rate Limiting**
   - Reduce following speed
   - Increase delay between actions
   - Use more proxies

## Support

For support, please:
1. Check the troubleshooting guide
2. Review the documentation
3. Open an issue in the repository
4. Contact the maintainers

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request
4. Follow the contribution guidelines

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Roadmap

- [ ] Enhanced proxy rotation
- [ ] Advanced analytics dashboard
- [ ] Automated account management
- [ ] Smart following algorithms
- [ ] Account health monitoring
- [ ] Performance optimization 