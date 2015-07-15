'use strict';

var PAGE_SIZE = 20;

var React = require('react');
var ReactBootstrap = require('react-bootstrap');
var $ = require('jquery');

var Glyphicon = ReactBootstrap.Glyphicon;
var ButtonGroup = ReactBootstrap.ButtonGroup;
var Button = ReactBootstrap.Button;
var Row = ReactBootstrap.Row;
var Col = ReactBootstrap.Col;
var Pagination = ReactBootstrap.Pagination;
var Modal = ReactBootstrap.Modal;
var Input = ReactBootstrap.Input;

var ContactBrowserApp = React.createClass({
    getInitialState: function () {
        return {
            count: 0,
            data: [],
            url: null,
            params: {},
            page: 1,
            busy: false,
            error: {},
            createFor: null,
            servers: [],
        };
    },
    displayError: function (url, method, xhr, status, err) {
        console.log(url, status, err);
        this.setState({
            busy: false,
            error: {
                url: url,
                xhr: xhr,
                status: status,
                err: err,
                method: method
            }
        });
    },
    loadData: function () {
        this.setState({busy: true});
        var data = JSON.parse(JSON.stringify(this.state.params));
        data["page"] = this.state.page;
        $.ajax({
            url: this.state.url,
            dataType: "json",
            data: data,
            success: function (response) {
                this.setState({busy: false,
                              data: response.results,
                              count: response.count,
                              next: response.next,
                              prev: response.prev});
            }.bind(this),
            error: function (xhr, status, err) {
                this.displayError(this.state.url, 'GET', xhr, status, err);
            }.bind(this)
        });
    },
    handleFormSubmit: function (data) {
        var serverDetails = this.refs.serverChooser.getServerDetail(data['server']);
        var url = serverDetails['url'] + data['type'] + "/";
        var params = {};
        if (data['email']) {
            params['email'] = data['email'];
        }
        if (data['name']) {
            params['name'] = data['name'];
        }
        if (data['type'] == 'release' && data['release_id']) {
            params['release'] = data['release_id'];
        }
        if (serverDetails['token']) {
            $.ajaxSetup({
                beforeSend: function (xhr, settings) {
                    xhr.setRequestHeader('Authorization', 'Token ' + serverDetails['token']);
                }
            });
        }
        this.setState({url: url, params: params, page: 1},
                      this.loadData);
    },
    handlePageChange: function (p) {
        this.setState({page: p}, this.loadData);
    },
    handleDelete: function (url) {
        this.setState({busy: true});
        $.ajax({
            url: url,
            method: "DELETE",
            success: this.loadData,
            error: function (xhr, status, err) {
                this.displayError(url, 'DELETE', xhr, status, err);
            }.bind(this)
        })
    },
    clearError: function () {
        this.setState({error: {}});
    },
    handleCreateStart: function (component) {
        this.setState({createFor: component});
    },
    handleContactSubmit: function (data) {
        var createFor = this.state.createFor;
        this.setState({busy: true, createFor: null}, function () {
            $.ajax({
                url: createFor.url + "contacts/",
                method: "POST",
                data: JSON.stringify(data),
                headers: {
                    "Content-Type": "application/json",
                },
                success: function (response) {
                    this.loadData();
                }.bind(this),
                error: function (xhr, status, err) {
                    this.displayError(createFor.url, "POST", xhr, status, err);
                }.bind(this)
            });
        });
    },
    clearCreate: function () {
        this.setState({createFor: null});
    },
    handleServerChange: function (servers) {
        this.setState({servers: servers});
    },
    render: function () {
        return (
            <div className="container-fluid">
                <ServerChooser ref="serverChooser" onServerChange={this.handleServerChange} />
                <LoadForm onSubmit={this.handleFormSubmit} servers={this.state.servers} />
                <Pager count={this.state.count} page={this.state.page} onPageChange={this.handlePageChange} />
                <Browser data={this.state.data} onDelete={this.handleDelete} onCreate={this.handleCreateStart} />
                <Pager count={this.state.count} page={this.state.page} onPageChange={this.handlePageChange} />
                <Spinner enabled={this.state.busy} />
                <NetworkErrorDialog onClose={this.clearError} data={this.state.error} />
                <ContactForm
                    onSubmit={this.handleContactSubmit}
                    createFor={this.state.createFor}
                    onClose={this.clearCreate} />
            </div>
        );
    }
});

var ServerChooser = React.createClass({
    getServerNames: function () {
        return Object.keys(this.state.servers).sort();
    },
    getServerDetail: function (name) {
        return this.state.servers[name];
    },
    getInitialState: function () {
        var servers = localStorage['pdc.servers'];
        servers = servers ? JSON.parse(servers) : {};
        this.props.onServerChange(Object.keys(servers).sort());
        return {visible: false, servers: servers};
    },
    handleVisibilityToggle: function () {
        this.setState({visible: !this.state.visible});
    },
    handleUpdate: function (oldName, newName, data) {
        var servers = this.state.servers;
        if (oldName && oldName in servers) {
            delete servers[oldName];
        }
        if (newName) {
            servers[newName] = data;
        }
        this.props.onServerChange(Object.keys(servers).sort());
        localStorage['pdc.servers'] = JSON.stringify(servers);
        this.setState({servers: servers});
    },
    render: function () {
        var dialog = null;
        if (this.state.visible) {
            var servers = [];
            var names = this.getServerNames();
            for (var idx in names) {
                var server = names[idx]
                servers.push(
                    <ServerSettings key={server}
                        name={server} data={this.state.servers[server]}
                        onChange={this.handleUpdate} />
                );
            }
            servers.push(<ServerSettings key="empty" data={{}} onChange={this.handleUpdate} />);
            dialog = (
                <Modal title="Server Setup"
                    onRequestHide={this.handleVisibilityToggle}>
                    <div className="modal-body">
                        {servers}
                    </div>
                    <div className='modal-footer'>
                        <Button onClick={this.handleVisibilityToggle}>Close</Button>
                    </div>
                </Modal>
            );
        }
        return (
            <div className="server-chooser-btn">
                <Button bsSize="large" bsStyle="link"
                    onClick={this.handleVisibilityToggle}>
                    <Glyphicon glyph="cog"/>
                </Button>
                {dialog}
            </div>
        );
    }
});

var ServerSettings = React.createClass({
    handleSave: function (e) {
        e.preventDefault();
        var data = {
            url: React.findDOMNode(this.refs.url).value,
            token: React.findDOMNode(this.refs.token).value
        };
        this.props.onChange(this.props.name, React.findDOMNode(this.refs.name).value, data);
        e.target.reset();
    },
    handleDelete: function (e) {
        e.preventDefault();
        this.props.onChange(this.props.name, null, null);
    },
    render: function () {
        var delBtn = <span />;
        if (this.props.name) {
            delBtn = <Button title="Delete" onClick={this.handleDelete}>
                <Glyphicon glyph="trash" />
            </Button>;
        }
        return (
            <form className="server-settings-row" onSubmit={this.handleSave}>
                <Row>
                    <Col sm={10}>
                        <Row>
                            <Col sm={4}>
                                <input className="form-control" type="text" placeholder="Server name"
                                    defaultValue={this.props.name} ref='name'
                                    onBlur={this.handleBlur} />
                            </Col>
                            <Col sm={8}>
                                <input className="form-control" type="url" placeholder="URL"
                                    defaultValue={this.props.data['url']} ref='url'
                                    onBlur={this.handleBlur} />
                            </Col>
                        </Row>
                        <Row>
                            <Col sm={12}>
                                <input className="form-control" type="text" placeholder="Token"
                                    defaultValue={this.props.data['token']} ref='token'
                                    onBlur={this.handleBlur} />
                            </Col>
                        </Row>
                    </Col>
                    <Col sm={2}>
                        <div className="btn-group-vertical">
                            <Button title="Save" type="Submit">
                                <Glyphicon glyph="save" />
                            </Button>
                            {delBtn}
                        </div>
                    </Col>
                </Row>
            </form>
        );
    }
});

var NetworkErrorDialog = React.createClass({
    handleClose: function () {
        this.props.onClose();
    },
    render: function () {
        if (Object.keys(this.props.data).length == 0) {
            return <div />;
        }
        var title = "Error: " + this.props.data.xhr.status + " " + this.props.data.err;
        var resp = <span />;
        if (this.props.data.xhr.responseJSON) {
            resp = (
                <div>
                    <p>The response was:</p>
                    <pre>{JSON.stringify(this.props.data.xhr.responseJSON, null, 2)}</pre>
                </div>
            );
        }
        return (
            <Modal
                title={title}
                className="error-dialog"
                onRequestHide={this.handleClose}>
                <div className="modal-body">
                    <p><b>{this.props.data.method}</b> <code>{this.props.data.url}</code></p>
                    {resp}
                </div>
                <div className='modal-footer'>
                    <Button onClick={this.handleClose}>Close</Button>
                </div>
            </Modal>
        );
    }
});

var ContactForm = React.createClass({
    getInitialState: function () {
        return {type: 'person'};
    },
    handleSubmit: function (e) {
        e.preventDefault();
        var data = {
            "contact_role": this.refs.role.getValue(),
            "contact": {
                "email": this.refs.email.getValue()
            }
        };
        if (this.refs.person.getChecked()) {
            data["contact"]["username"] = this.refs.username.getValue();
        } else {
            data["contact"]["mailname"] = this.refs.mailname.getValue();
        }
        this.props.onSubmit(data);
    },
    handleCancel: function () {
        this.props.onClose();
    },
    handleTypeChange: function (focus, event) {
        this.setState({type: event.target.value}, function () {
            this.refs[focus].getInputDOMNode().focus();
        });
    },
    render: function () {
        if (!this.props.createFor) {
            return <div />;
        }
        var name = null;
        if ('release' in this.props.createFor) {
            name = this.props.createFor.release.release_id + "/" + this.props.createFor.name;
        } else {
            name = this.props.createFor.name;
        }
        var title = "Create new contact for " + name;
        return (
            <form onSubmit={this.handleSubmit}>
                <Modal
                    title={title}
                    bsSize="large"
                    onRequestHide={this.handleCancel}>
                    <div className="modal-body">
                        <Input type="text" ref="role" label="Role" required />
                        <Input type="email" ref="email" label="E-mail" required />
                        <Row>
                            <Col md={6}>
                                <Input type='radio' name="type" value="person" ref="person" label='Person'
                                    defaultChecked onChange={this.handleTypeChange.bind(this, "username")} />
                                <Input type='text' ref="username" label='Username' required
                                    disabled={this.state.type != "person"} />
                            </Col>
                            <Col md={6}>
                                <Input type='radio' name="type" value="maillist" ref="maillist"
                                    label='Mailing list'
                                    onChange={this.handleTypeChange.bind(this, "mailname")} />
                                <Input type='text' ref="mailname" label='Mailing list name' required
                                    disabled={this.state.type != "maillist"} />
                            </Col>
                        </Row>
                    </div>
                    <div className="modal-footer">
                        <Button bsStyle="link" onClick={this.handleCancel}>Close</Button>
                        <Button bsStyle="primary" type="submit">Create</Button>
                    </div>
                </Modal>
            </form>
        );
    }
});

var Spinner = React.createClass({
    render: function () {
        if (this.props.enabled) {
            return (
                <div className='overlay'>
                    <div className='spinner-loader'>Loading …</div>
                </div>
            );
        } else {
            return (<div />);
        }
    }
});

var Pager = React.createClass({
    handlePageChange: function (event, selectedEvent) {
        event.preventDefault()
        this.props.onPageChange(selectedEvent.eventKey);
    },
    render: function () {
        if (this.props.count == 0) {
            return <div />;
        }
        var n_pages = Math.ceil(this.props.count / PAGE_SIZE);
        return (
            <Row>
                <Col md={6}>
                    <p className="count-text">{this.props.count} components</p>
                </Col>
                <Col md={6} className="text-right">
                    <Pagination
                        items={n_pages}
                        activePage={this.props.page}
                        onSelect={this.handlePageChange} />
                </Col>
            </Row>
        );
    }
});

var LoadForm = React.createClass({
    getInitialState: function () {
        return {globalComponents: true};
    },
    handleTypeToggle: function (e) {
        React.findDOMNode(this.refs.release_id).value = '';
        this.setState({globalComponents: e.target.id == "global"});
    },
    handleSubmit: function (e) {
        e.preventDefault();
        var data = {
            'server': React.findDOMNode(this.refs.server).value,
            'email': React.findDOMNode(this.refs.email).value,
            'name': React.findDOMNode(this.refs.name).value,
            'type': React.findDOMNode(this.refs.global).checked ? 'global-components' : 'release-components',
            'release_id': React.findDOMNode(this.refs.release_id).value
        };
        if (!data['server']) {
            return;
        }
        this.props.onSubmit(data);
    },
    render: function () {
        var disabled = this.state.globalComponents ? "disabled" : "";
        var opts = this.props.servers.map(function (val) {
            return <option key={val}>{val}</option>;
        });
        return (
            <Row className="loadForm">
                <Col md={8} mdOffset={2}>
                    <form className="form-horizontal" onSubmit={this.handleSubmit}>
                        <div className="form-group">
                            <label htmlFor="server" className="col-sm-2 control-label">Server</label>
                            <Col sm={10}>
                                <select className="form-control" id="server" ref="server" required="required">
                                    {opts}
                                </select>
                            </Col>
                        </div>
                        <div className="form-group">
                            <label htmlFor="email" className="col-sm-2 control-label">E-mail</label>
                            <div className="col-sm-10">
                                <input type="email" className="form-control" id="email" ref="email" />
                            </div>
                        </div>
                        <div className="form-group">
                            <label htmlFor="name" className="col-sm-2 control-label">Component Name</label>
                            <Col sm={10}>
                                <input type="text" className="form-control" id="name" ref="name" />
                            </Col>
                        </div>
                        <div className="form-group">
                            <Col smOffset={2} sm={10}>
                                <label className="radio-inline">
                                    <input type="radio" name="type" id="global" ref="global"
                                        defaultChecked="true" onChange={this.handleTypeToggle} />
                                    Global Components
                                </label>
                                <label className="radio-inline">
                                    <input type="radio" name="type" id="release"
                                        onChange={this.handleTypeToggle} />
                                    Release Components
                                </label>
                            </Col>
                        </div>
                        <div className="form-group">
                            <label htmlFor="release_id" className="col-sm-2 control-label">Release</label>
                            <Col sm={10}>
                                <input type="text" className="form-control" id="release_id" ref="release_id"
                                    aria-describedby="helpBlock"
                                    disabled={disabled} />
                                <span id="helpBlock" className="help-block">
                                    Only display components from this release. If left empty, all releases
                                    will be processed.
                                </span>
                            </Col>
                        </div>
                        <div className="form-group">
                            <Col smOffset={2} sm={10}>
                                <Button type="submit">Load components</Button>
                            </Col>
                        </div>
                    </form>
                </Col>
            </Row>
        );
    }
});

var Browser = React.createClass({
    handleDelete: function (url) {
        this.props.onDelete(url);
    },
    handleCreate: function (component) {
        this.props.onCreate(component);
    },
    render: function () {
        var components = this.props.data.map(function (c) {
            return (
                <ComponentView key={c.url} data={c}
                    onDelete={this.handleDelete}
                    onCreate={this.handleCreate} />
            );
        }.bind(this));
        return (
            <div>
                {components}
            </div>
        );
    }
});

var ComponentView = React.createClass({
    handleDelete: function (url) {
        this.props.onDelete(url);
    },
    handleCreate: function (e) {
        this.props.onCreate(this.props.data);
    },
    render: function () {
        var contacts = this.props.data.contacts.map(function (c) {
            return (<ContactView key={c.url} data={c} onDelete={this.handleDelete} />);
        }.bind(this));
        var name = this.props.data.name;
        if ("release" in this.props.data) {
            name = this.props.data.release.release_id + "/" + this.props.data.name;
        }
        return (
            <div>
                <h2>
                    {name}
                    <Button onClick={this.handleCreate}><Glyphicon glyph="pencil" /> Create</Button>
                </h2>
                <table className="table">
                    <thead>
                        <tr>
                            <th></th>
                            <th>Name</th>
                            <th>E-mail</th>
                            <th>Role</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        {contacts}
                    </tbody>
                </table>
            </div>
        );
    }
});

var ContactView = React.createClass({
    handleDelete: function (e) {
        e.preventDefault();
        this.props.onDelete(this.props.data.url);
    },
    render: function () {
        var inherited = <span />
        if ("inherited" in this.props.data && this.props.data.inherited) {
            inherited = <Glyphicon glyph="link" title="Inherited from global component" />;
        }
        var name = "username" in this.props.data.contact
            ? this.props.data.contact.username
            : this.props.data.contact.mail_name;
        return (
            <tr>
                <td><p className="form-control-static text-center">{inherited}</p></td>
                <td><p className="form-control-static">{name}</p></td>
                <td><p className="form-control-static">{this.props.data.contact.email}</p></td>
                <td><p className="form-control-static">{this.props.data.contact_role}</p></td>
                <td>
                    <Button title="Delete" onClick={this.handleDelete}>
                        <Glyphicon glyph="trash" />
                    </Button>
                </td>
            </tr>
        );
    }
});

React.render(
    <ContactBrowserApp url="http://localhost:8000/rest_api/v1/" />,
    document.getElementById('app')
);
