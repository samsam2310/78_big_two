(function(){
    console.log('init');
    var Table = React.createClass({
        render: function() {
            var cards = this.props.cards.map(function(v){
                return (<span className={'card'}>{v}</span>);
            });
            return (<div className={'current_card'}><span className={'current_card_title'}>Current Card</span><div className={'current_card_board'}>{cards}</div></div>);
        }
    });
    var CountDown = React.createClass({
        getInitialState: function() {
            return {time: 0};
        },
        componentDidMount: function(nprop){
            this._mount = true;
            this.updateTime();
        },
        componentWillUnmount: function(){
            this._mount = false;
        },
        getTime: function(){
            var local = new Date().getTime()/1000;
            return local + this.props.delay;
        },
        updateTime: function(){
            var time = this.props.deadline - this.getTime();
            if(time < 0)time = 0;
            this.setState({time: time});
            if(this._mount)setTimeout(this.updateTime, 50);
        },
        render: function() {
            var time = 'OK';
            if(this.props.deadline != 0)time = this.props.deadline - this.getTime();
            if(time < 0)time = 0;
            return (<span>{this.state.time.toFixed(1)}</span>);
        }
    });
    var Player = React.createClass({
        render: function() {
            var turn = (<span className={'not-turn'}>Not Turn</span>);
            if(this.props.turn_num == this.props.index)turn = <span className={'turn'}>Turn!</span>
            return (
                <div className={'player'}>
                    <span className={'player-name'}>{this.props.player['name']}</span>
                    <span className={'player-card'}>
                        <span className={'card_icon'}></span>
                        <span className={'card_num'}>{this.props.player['card']}</span>
                    </span>
                    <span className={Number(this.props.player['conn'])==1?'avail player-conn':'unavail player-conn'}>
                        {Number(this.props.player['conn'])==1?'Online':'Offline'}
                    </span>
                    {turn}
                    <CountDown delay={this.props.delay} deadline={this.props.player.deadline}/>
                </div>
            );
        }
    });
    var Control = React.createClass({
        getInitialState: function() {
            return {
                status: []
            };
        },
        componentWillReceiveProps: function(nxtProp) {
            if(nxtProp.cards)this.setState({status: []});
        },
        handleTrow: function(type){
            console.log('handle '+type);
            var ch_cs = [];
            for(var i in this.props.cards){
                if(this.state.status[i])ch_cs.push(this.props.cards[i])
            }
            this.props.onClick({type: type, card: ch_cs});
        },
        render: function() {
            var that = this;
            var ch_c = this.props.cards.map(function(v, i){
                if(that.state.status[i]){
                    return (<span className={'card'}>{v}</span>);
                }
                return (<span/>);
            });
            var card = this.props.cards.map(function(v, i){
                var click = function(){
                    var status = that.state.status.slice();
                    status[i] = !status[i];
                    that.setState({status: status});
                }
                return (<button onClick={click}>{v}</button>);
            });
            var that = this;
            var start_btn = null;
            if(this.props.start_btn){
                start_btn = (<button className={'btn btn-success btn-start'}
                    onClick={function(){that.props.onClick({'type':'start'})}}>開始</button>);
            }
            var reset_btn = null;
            if(this.props.reset_btn){
                reset_btn = (<button className={'btn btn-danger btn-reset'}
                    onClick={function(){that.props.onClick({'type':'reset'})}}>重設</button>);
            }
            return (
                <div>
                    <h4 className={'name'}>{this.props.name}</h4>
                    <div className={'user_card'}>{ch_c}</div>
                    <div className={'user_card_set'}>{card}</div>
                    <div>
                      <div className={'form-inline'}>
                        <div className={'form-group'}>{start_btn}</div>
                        <div className={'form-group'}>{reset_btn}</div>
                        <div className={'form-group'}><button className={'btn btn-info btn-change'} disabled={!this.props.is_your_turn} onClick={function(){that.handleTrow('change')}}>換牌</button></div>
                        <div className={'form-group'}><button className={'btn btn-info btn-throw'} disabled={!this.props.is_your_turn} onClick={function(){that.handleTrow('throw')}}>出牌</button></div>
                        <div className={'form-group'}><button className={'btn btn-info btn-pick'} disabled={!this.props.is_your_turn} onClick={function(){that.props.onClick({'type':'pick'})}}>抽牌</button></div>
                      </div>
                    </div>
                </div>
            );
        }
    });
    var GameTable = React.createClass({
        getInitialState: function() {
            return {
                status: '?',
                your_name: 'Name',
                your_card: ['0A','4K'],
                current_card: ['3K','2K'],
                turn: '',
                turn_num: -1,
                players: [{name: 'a', card: 2},{name: 'b', card: 2}],
                room_manager: 'Manager',
                online_user: 0,
                delay: 0,
            };
        },
        componentDidMount: function() {
            var url = 'ws://' + window.location.host + '/gamesocket'
            var conn = new WebSocket(url);
            this.send = function(json) {
                conn.send(JSON.stringify(json));
            };
            this.socketState = function(){
                return conn.readyState;
            };
            var that = this;
            conn.onmessage = function(evt) {
                var json = JSON.parse(evt.data);
                that.handleMessage(json);
            };
            setTimeout(this.syncTime, 1000);
        },
        syncTime: function(){
            var state = this.socketState();
            if(state == 1)this.send({'req': 'synctime', 'time': new Date().getTime()/1000});
            if(state <= 1)setTimeout(this.syncTime, 10000);
        },
        handleMessage: function(json) {
            if(json.$set){
                console.log("Set!!!");
                console.log(json);
                this.setState(json.$set);
            }
        },
        handleClick: function(cli) {
            if(cli.type=='start'){
                this.send({'req': 'start'});
            }else if(cli.type=='reset'){
                this.send({'req': 'reset'});
            }else if(cli.type=='throw'){
                this.send({'req': 'throw', card: cli.card});
                console.log('throw');
                console.log(cli.card);
            }else if(cli.type=='change'){
                this.send({'req': 'change', card: cli.card});
            }else if(cli.type=='pick'){
                this.send({'req': 'pick'});
                console.log('pick');
            }
        },
        render: function() {
            var that = this;
            var players = this.state.players.map(function(v, i){
                return (<Player index={i} player={v} turn_num={that.state.turn_num} delay={that.state.delay}/>);
            });
            return (<div className={'thegame'}>
                <div className={'status'}><span className={'attr_title'}>Status</span>{this.state.status}</div>
                <Table cards={this.state.current_card}/>
                <div className={'gametable'}>
                {players}
                </div>
                <Control name={this.state.your_name}
                    cards={this.state.your_card}
                    start_btn={this.state.your_name==this.state.room_manager && this.state.status=='init'}
                    reset_btn={this.state.your_name==this.state.room_manager && this.state.status=='gameover'}
                    onClick={this.handleClick}
                    is_your_turn={this.state.turn==this.state.your_name}/>
            </div>);
        }
    });
    ReactDOM.render(
        <GameTable />,
        document.getElementById('groot')
    );
    console.log('init-end');
}())
